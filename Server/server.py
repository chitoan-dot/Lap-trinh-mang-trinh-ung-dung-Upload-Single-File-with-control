import customtkinter as ctk
from tkinter import filedialog
import socket
import threading
import os
import shutil
import struct
import time
import json
from datetime import datetime

COLORS = {
    "bg": "#0B111A",
    "surface": "#121A26",
    "surface_2": "#182231",
    "surface_3": "#202C3D",
    "border": "#2C3B50",
    "text": "#F4F7FB",
    "muted": "#A7B6CB",
    "subtle": "#72839B",
    "primary": "#4F8CFF",
    "primary_hover": "#3B73E6",
    "success": "#2ECC71",
    "warning": "#F4B860",
    "danger": "#F05D5E",
    "danger_hover": "#D94A4B",
    "button_text": "#FFFFFF",
    "button_disabled_text": "#D7E2F2",
}

SERVER_ERROR_OFFSET = (1 << 64) - 1
MIN_FREE_SPACE_BUFFER = 5 * 1024 * 1024
SERVER_CONFIG_FILE = "server_config.json"

TRANSFER_COLUMNS = (
    {"weight": 1, "minsize": 260},
    {"weight": 0, "minsize": 170},
    {"weight": 0, "minsize": 300},
    {"weight": 0, "minsize": 120},
    {"weight": 0, "minsize": 150},
)


class ServerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Máy chủ nhận tệp")
        self.geometry("1180x720")
        self.minsize(1020, 660)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg"])

        self.server_socket = None
        self.listen_thread = None
        self.running = False
        self.clients = {}
        self.client_rows = {}
        self.transfer_rows = {}
        self.transfer_states = {}
        self.total_files = 0
        self.total_bytes = 0
        self.failed_uploads = 0
        self.started_at = None
        self.upload_dir = os.path.abspath("Uploads")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_dashboard()
        self.build_content()
        self.load_config()
        self.refresh_server_address()

        self.log("Bảng điều khiển máy chủ đã sẵn sàng.")
        self.update_dashboard()
        self.update_uptime()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=74)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        logo = ctk.CTkFrame(header, fg_color=COLORS["primary"], width=38, height=38, corner_radius=11)
        logo.grid(row=0, column=0, padx=(22, 12), pady=18)
        logo.grid_propagate(False)
        ctk.CTkLabel(logo, text="SV", font=ctk.CTkFont(size=12, weight="bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(title_box, text="Máy chủ nhận tệp", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Theo dõi thiết bị gửi, phiên nhận và dữ liệu lưu trữ", font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w")

        config = ctk.CTkFrame(header, fg_color="transparent")
        config.grid(row=0, column=2, padx=(10, 6), pady=16, sticky="e")
        self.ip_entry = ctk.CTkEntry(config, width=132, height=36, placeholder_text="0.0.0.0", fg_color=COLORS["surface_2"], border_color=COLORS["border"])
        self.ip_entry.insert(0, "0.0.0.0")
        self.ip_entry.grid(row=0, column=0, padx=4)
        self.port_entry = ctk.CTkEntry(config, width=86, height=36, placeholder_text="8888", fg_color=COLORS["surface_2"], border_color=COLORS["border"])
        self.port_entry.insert(0, "8888")
        self.port_entry.grid(row=0, column=1, padx=4)
        self.copy_address_button = ctk.CTkButton(config, text="Copy IP", command=self.copy_server_address, width=86, height=36, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.copy_address_button.grid(row=0, column=2, padx=4)

        self.status_pill = ctk.CTkLabel(header, text="ĐÃ DỪNG", width=112, fg_color=COLORS["surface_3"], text_color=COLORS["warning"], corner_radius=16, padx=14, height=32, font=ctk.CTkFont(size=12, weight="bold"))
        self.status_pill.grid(row=0, column=3, padx=8, sticky="e")

        self.start_button = ctk.CTkButton(header, text="Bắt đầu", command=self.start_server, width=118, height=38, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.start_button.grid(row=0, column=4, padx=(8, 4), sticky="e")
        self.stop_button = ctk.CTkButton(header, text="Dừng", command=self.stop_server, width=104, height=38, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"], state=ctk.DISABLED)
        self.stop_button.grid(row=0, column=5, padx=(4, 22), sticky="e")

    def get_lan_ip(self):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            ip = probe.getsockname()[0]
            probe.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def refresh_server_address(self):
        address = f"{self.get_lan_ip()}:{self.port_entry.get().strip() or '8888'}"
        if hasattr(self, "server_address_label"):
            self.server_address_label.configure(text=f"Địa chỉ LAN: {address}")

    def copy_server_address(self):
        address = f"{self.get_lan_ip()}:{self.port_entry.get().strip() or '8888'}"
        self.clipboard_clear()
        self.clipboard_append(address)
        self.log(f"Đã copy địa chỉ máy chủ: {address}", "SUCCESS")

    def build_dashboard(self):
        dashboard = ctk.CTkFrame(self, fg_color="transparent")
        dashboard.grid(row=1, column=0, padx=18, pady=(18, 10), sticky="ew")
        for index in range(6):
            dashboard.grid_columnconfigure(index, weight=1)

        self.active_clients_value = self.create_stat_card(dashboard, 0, "Thiết bị gửi", "0")
        self.active_transfers_value = self.create_stat_card(dashboard, 1, "Đang nhận", "0")
        self.total_files_value = self.create_stat_card(dashboard, 2, "Tệp đã nhận", "0")
        self.total_data_value = self.create_stat_card(dashboard, 3, "Dữ liệu đã nhận", "0 B")
        self.failed_value = self.create_stat_card(dashboard, 4, "Lỗi", "0")
        self.uptime_value = self.create_stat_card(dashboard, 5, "Thời gian", "--")

    def create_stat_card(self, parent, column, label, value):
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=16)
        card.grid(row=0, column=column, padx=5, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=label, text_color=COLORS["muted"], font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")
        value_label = ctk.CTkLabel(card, text=value, text_color=COLORS["text"], font=ctk.CTkFont(size=20, weight="bold"))
        value_label.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")
        return value_label

    def browse_upload_dir(self):
        folder = filedialog.askdirectory(parent=self, initialdir=self.upload_dir)
        if not folder:
            return
        self.upload_dir = os.path.abspath(folder)
        self.upload_dir_entry.delete(0, "end")
        self.upload_dir_entry.insert(0, self.upload_dir)
        self.save_config()
        self.log(f"Đã chọn thư mục lưu: {self.upload_dir}", "SUCCESS")

    def save_config(self):
        config = {
            "server_ip": self.ip_entry.get().strip(),
            "server_port": self.port_entry.get().strip(),
            "upload_dir": self.upload_dir_entry.get().strip() if hasattr(self, "upload_dir_entry") else self.upload_dir,
        }
        try:
            with open(SERVER_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"Lỗi khi lưu cấu hình máy chủ: {e}", "ERROR")

    def load_config(self):
        config = {
            "server_ip": "0.0.0.0",
            "server_port": "8888",
            "upload_dir": self.upload_dir,
        }
        try:
            if os.path.exists(SERVER_CONFIG_FILE):
                with open(SERVER_CONFIG_FILE, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
        except Exception as e:
            self.log(f"Lỗi khi tải cấu hình máy chủ: {e}", "ERROR")

        self.ip_entry.delete(0, "end")
        self.ip_entry.insert(0, config["server_ip"])
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, config["server_port"])
        self.upload_dir = os.path.abspath(config["upload_dir"] or "Uploads")
        self.upload_dir_entry.delete(0, "end")
        self.upload_dir_entry.insert(0, self.upload_dir)

    def build_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        content.grid_columnconfigure(0, minsize=290)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        clients_card = ctk.CTkFrame(content, fg_color=COLORS["surface"], corner_radius=16)
        clients_card.grid(row=0, column=0, padx=(0, 14), sticky="nsew")
        clients_card.grid_columnconfigure(0, weight=1)
        clients_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(clients_card, text="Thiết bị gửi đang kết nối", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"]).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        storage = ctk.CTkFrame(clients_card, fg_color=COLORS["surface_2"], corner_radius=14)
        storage.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
        storage.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(storage, text="Thư mục lưu tệp", text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="w")
        self.upload_dir_entry = ctk.CTkEntry(storage, height=34, fg_color=COLORS["surface"], border_color=COLORS["border"])
        self.upload_dir_entry.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="ew")
        self.browse_upload_dir_button = ctk.CTkButton(storage, text="Chọn", command=self.browse_upload_dir, width=72, height=34, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.browse_upload_dir_button.grid(row=1, column=1, padx=(6, 12), pady=(0, 12))
        self.server_address_label = ctk.CTkLabel(storage, text="", text_color=COLORS["subtle"], font=ctk.CTkFont(size=11), anchor="w")
        self.server_address_label.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

        self.clients_frame = ctk.CTkScrollableFrame(clients_card, fg_color="transparent")
        self.clients_frame.grid(row=2, column=0, padx=12, pady=(0, 14), sticky="nsew")
        self.clients_frame.grid_columnconfigure(0, weight=1)
        self.empty_clients_label = ctk.CTkLabel(self.clients_frame, text="Chưa có thiết bị gửi kết nối.", text_color=COLORS["subtle"])
        self.empty_clients_label.grid(row=0, column=0, pady=32)

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(right, fg_color=COLORS["surface"], segmented_button_fg_color=COLORS["surface_2"], segmented_button_selected_color=COLORS["primary"], segmented_button_selected_hover_color=COLORS["primary_hover"])
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.tab_view.add("Phiên nhận")
        self.tab_view.add("Nhật ký")

        self.build_transfers_tab()
        self.build_logs_tab()

    def build_transfers_tab(self):
        tab = self.tab_view.tab("Phiên nhận")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(tab, fg_color=COLORS["surface_2"], corner_radius=8)
        header.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        header.grid_propagate(False)
        header.configure(height=46)
        header.grid_rowconfigure(0, weight=1)
        self.configure_transfer_columns(header)
        header_specs = (
            ("Tệp", "w"),
            ("Thiết bị gửi", "center"),
            ("Tiến trình", "center"),
            ("Tốc độ", "center"),
            ("Trạng thái", "center"),
        )
        for column, (text, anchor) in enumerate(header_specs):
            ctk.CTkLabel(header, text=text, text_color=COLORS["muted"], font=ctk.CTkFont(size=11, weight="bold"), anchor=anchor).grid(row=0, column=column, padx=12, sticky="nsew")

        self.transfers_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.transfers_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.transfers_frame.grid_columnconfigure(0, weight=1)
        self.empty_transfers_label = ctk.CTkLabel(self.transfers_frame, text="Chưa có phiên nhận nào.", text_color=COLORS["subtle"])
        self.empty_transfers_label.grid(row=0, column=0, pady=32)

    def configure_transfer_columns(self, container):
        for index, options in enumerate(TRANSFER_COLUMNS):
            container.grid_columnconfigure(index, weight=options["weight"], minsize=options["minsize"])

    def build_logs_tab(self):
        tab = self.tab_view.tab("Nhật ký")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(toolbar, text="Nhật ký sự kiện", text_color=COLORS["text"], font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(toolbar, text="Xóa", command=self.clear_logs, width=96, height=30, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"]).grid(row=0, column=1, sticky="e")

        self.log_area = ctk.CTkTextbox(tab, fg_color=COLORS["bg"], text_color=COLORS["muted"], border_width=1, border_color=COLORS["border"], corner_radius=12, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_area.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_area.configure(state="disabled")
        try:
            self.log_area.tag_config("INFO", foreground=COLORS["muted"])
            self.log_area.tag_config("WARN", foreground=COLORS["warning"])
            self.log_area.tag_config("ERROR", foreground=COLORS["danger"])
            self.log_area.tag_config("SUCCESS", foreground=COLORS["success"])
        except Exception:
            pass

    def start_server(self):
        ip = self.ip_entry.get().strip()
        port_text = self.port_entry.get().strip()
        if not port_text.isdigit():
            self.log("Cổng không hợp lệ.", "ERROR")
            return

        port = int(port_text)
        self.running = True
        self.upload_dir = os.path.abspath(self.upload_dir_entry.get().strip() or "Uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self.save_config()

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((ip, port))
            self.server_socket.listen(10)

            self.started_at = time.time()
            self.listen_thread = threading.Thread(target=self.listen_for_clients, daemon=True)
            self.listen_thread.start()

            self.status_pill.configure(text="ĐANG CHẠY", fg_color=COLORS["success"], text_color="white")
            self.start_button.configure(state=ctk.DISABLED)
            self.stop_button.configure(state=ctk.NORMAL)
            self.ip_entry.configure(state=ctk.DISABLED)
            self.port_entry.configure(state=ctk.DISABLED)
            self.upload_dir_entry.configure(state=ctk.DISABLED)
            self.browse_upload_dir_button.configure(state=ctk.DISABLED)
            self.log(f"Máy chủ đang lắng nghe tại {ip}:{port}", "SUCCESS")
            self.refresh_server_address()
            self.update_dashboard()
        except Exception as e:
            self.running = False
            self.server_socket = None
            self.log(f"Không thể khởi động máy chủ: {e}", "ERROR")
            self.status_pill.configure(text="LỖI", fg_color=COLORS["danger"], text_color="white")

    def stop_server(self):
        if not self.running and not self.server_socket:
            return

        self.running = False
        for addr, client_socket in list(self.clients.items()):
            try:
                client_socket.close()
            except Exception:
                pass
            self.log(f"Đã đóng kết nối tới {self.format_addr(addr)}", "WARN")

        self.clients.clear()
        self.refresh_clients_panel()

        if self.server_socket:
            try:
                dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dummy_socket.settimeout(1)
                dummy_socket.connect((self.get_unblock_ip(), int(self.port_entry.get())))
                dummy_socket.close()
            except Exception:
                pass
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        self.status_pill.configure(text="ĐÃ DỪNG", fg_color=COLORS["surface_3"], text_color=COLORS["warning"])
        self.start_button.configure(state=ctk.NORMAL)
        self.stop_button.configure(state=ctk.DISABLED)
        self.ip_entry.configure(state=ctk.NORMAL)
        self.port_entry.configure(state=ctk.NORMAL)
        self.upload_dir_entry.configure(state=ctk.NORMAL)
        self.browse_upload_dir_button.configure(state=ctk.NORMAL)
        self.log("Máy chủ đã dừng.", "WARN")
        self.update_dashboard()

    def listen_for_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                if not self.running:
                    try:
                        client_socket.close()
                    except Exception:
                        pass
                    break

                self.clients[addr] = client_socket
                self.log(f"Đã nhận kết nối từ {self.format_addr(addr)}")
                self.refresh_clients_panel()
                self.update_dashboard()

                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True)
                client_handler.start()
            except OSError:
                if self.running:
                    self.log("Lỗi khi nhận kết nối.", "ERROR")
                break

    def handle_client(self, client_socket, addr):
        transfer_key = self.format_addr(addr)
        try:
            command_byte = self.recv_exact(client_socket, 1)
            command = command_byte.decode(errors="replace")

            if command != "U":
                self.log(f"Lệnh không xác định '{command}' từ {transfer_key}", "WARN")
                return

            dir_name_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            target_dir = self.recv_exact(client_socket, dir_name_len).decode(errors="replace") if dir_name_len > 0 else ""

            file_name_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            file_name = self.recv_exact(client_socket, file_name_len).decode(errors="replace")
            file_size = struct.unpack("!Q", self.recv_exact(client_socket, 8))[0]
            duplicate_policy = self.recv_exact(client_socket, 1).decode(errors="replace") or "R"

            safe_target_dir = self.sanitize_subfolder(target_dir)
            safe_file_name = os.path.basename(file_name)
            self.log(f"{transfer_key} đang gửi '{safe_file_name}' ({self.format_bytes(file_size)}) vào '{safe_target_dir or 'Uploads'}'")

            base_upload_dir = self.upload_dir
            final_dir = os.path.join(base_upload_dir, safe_target_dir)
            os.makedirs(final_dir, exist_ok=True)
            file_path = os.path.join(final_dir, safe_file_name)

            offset = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            if os.path.exists(file_path) and duplicate_policy == "O":
                offset = 0
            elif os.path.exists(file_path) and duplicate_policy == "N":
                file_path = self.unique_file_path(final_dir, safe_file_name)
                safe_file_name = os.path.basename(file_path)
                offset = 0
            elif os.path.exists(file_path) and duplicate_policy == "S":
                offset = file_size

            remaining_size = max(file_size - offset, 0)
            free_space = shutil.disk_usage(final_dir).free
            if remaining_size > 0 and free_space < remaining_size + MIN_FREE_SPACE_BUFFER:
                client_socket.sendall(struct.pack("!Q", SERVER_ERROR_OFFSET))
                self.failed_uploads += 1
                self.log(
                    f"Không đủ dung lượng để nhận '{safe_file_name}'. Cần {self.format_bytes(remaining_size)}, còn trống {self.format_bytes(free_space)}.",
                    "ERROR",
                )
                self.update_dashboard()
                return

            client_socket.sendall(struct.pack("!Q", offset))

            self.create_transfer_row(transfer_key, safe_file_name, file_size)
            if offset >= file_size:
                self.total_files += 1
                self.update_transfer_row(transfer_key, progress=1, speed="0.00 MB/s", state="Đã bỏ qua", color=COLORS["success"])
                self.log(f"Đã bỏ qua '{safe_file_name}' vì file đã tồn tại.", "WARN")
                self.update_dashboard()
                return

            mode = "wb" if duplicate_policy in ("O", "N") and offset == 0 else "ab"
            with open(file_path, mode) as f:
                f.seek(offset)
                received_bytes = offset
                last_update_time = time.time()
                last_sample_bytes = received_bytes

                while received_bytes < file_size:
                    data = client_socket.recv(65536)
                    if not data:
                        raise ConnectionAbruptlyClosed("Thiết bị gửi đã đóng kết nối khi đang gửi tệp.")

                    f.write(data)
                    received_bytes += len(data)
                    self.total_bytes += len(data)

                    now = time.time()
                    elapsed = now - last_update_time
                    if elapsed >= 0.35 or received_bytes == file_size:
                        delta = received_bytes - last_sample_bytes
                        speed = delta / elapsed if elapsed > 0 else 0
                        progress = received_bytes / file_size if file_size else 1
                        self.update_transfer_row(
                            transfer_key,
                            progress=progress,
                            speed=f"{speed / (1024 * 1024):.2f} MB/s",
                            state="Đang nhận",
                            color=COLORS["primary"],
                        )
                        self.update_dashboard()
                        last_update_time = now
                        last_sample_bytes = received_bytes

            self.total_files += 1
            self.update_transfer_row(transfer_key, progress=1, speed="0.00 MB/s", state="Hoàn tất", color=COLORS["success"])
            self.log(f"Đã nhận xong '{safe_file_name}' từ {transfer_key}.", "SUCCESS")
            self.update_dashboard()

        except ConnectionAbruptlyClosed as e:
            self.failed_uploads += 1
            self.update_transfer_row(transfer_key, state="Lỗi", color=COLORS["danger"])
            self.log(f"Thiết bị gửi {transfer_key} ngắt kết nối đột ngột: {e}", "WARN")
            self.update_dashboard()
        except Exception as e:
            self.failed_uploads += 1
            self.update_transfer_row(transfer_key, state="Lỗi", color=COLORS["danger"])
            self.log(f"Lỗi khi xử lý thiết bị gửi {transfer_key}: {e}", "ERROR")
            self.update_dashboard()
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
            if addr in self.clients:
                del self.clients[addr]
            self.log(f"Kết nối với {transfer_key} đã đóng.")
            self.refresh_clients_panel()
            self.update_dashboard()

    def create_transfer_row(self, key, file_name, file_size):
        def _create():
            if self.empty_transfers_label.winfo_exists():
                self.empty_transfers_label.grid_forget()
            if key in self.transfer_rows:
                self.transfer_rows[key]["row"].destroy()
            self.transfer_states[key] = "Đang nhận"

            row = ctk.CTkFrame(self.transfers_frame, fg_color=COLORS["surface_2"], corner_radius=10, height=58)
            row.grid(row=len(self.transfer_rows), column=0, pady=5, sticky="ew")
            row.grid_propagate(False)
            row.grid_rowconfigure(0, weight=1)
            self.configure_transfer_columns(row)

            file_label = ctk.CTkLabel(row, text=file_name, text_color=COLORS["text"], anchor="w")
            file_label.grid(row=0, column=0, padx=(14, 12), sticky="nsew")
            client_label = ctk.CTkLabel(row, text=key, text_color=COLORS["muted"], anchor="center")
            client_label.grid(row=0, column=1, padx=12, sticky="nsew")
            progress = ctk.CTkProgressBar(row, height=10, fg_color=COLORS["surface_3"], progress_color=COLORS["primary"], corner_radius=6)
            progress.grid(row=0, column=2, padx=18, sticky="ew")
            progress.set(0)
            speed = ctk.CTkLabel(row, text="0.00 MB/s", text_color=COLORS["muted"], anchor="center")
            speed.grid(row=0, column=3, padx=12, sticky="nsew")
            state = ctk.CTkLabel(row, text="Đang nhận", width=118, text_color=COLORS["text"], fg_color=COLORS["primary"], corner_radius=12, padx=10, height=28)
            state.grid(row=0, column=4, padx=(12, 14), sticky="")

            self.transfer_rows[key] = {
                "row": row,
                "file": file_label,
                "client": client_label,
                "progress": progress,
                "speed": speed,
                "state": state,
            }

        self.after(0, _create)

    def update_transfer_row(self, key, progress=None, speed=None, state=None, color=None):
        if state is not None:
            self.transfer_states[key] = state

        def _update():
            widgets = self.transfer_rows.get(key)
            if not widgets:
                return
            if progress is not None:
                widgets["progress"].set(progress)
            if speed is not None:
                widgets["speed"].configure(text=speed)
            if state is not None:
                widgets["state"].configure(text=state, fg_color=color or COLORS["surface_3"], text_color=COLORS["text"])

        self.after(0, _update)

    def refresh_clients_panel(self):
        def _refresh():
            for row in self.client_rows.values():
                row.destroy()
            self.client_rows.clear()

            if not self.clients:
                self.empty_clients_label.grid(row=0, column=0, pady=32)
                return
            self.empty_clients_label.grid_forget()

            for index, addr in enumerate(self.clients.keys()):
                row = ctk.CTkFrame(self.clients_frame, fg_color=COLORS["surface_2"], corner_radius=12)
                row.grid(row=index, column=0, pady=5, sticky="ew")
                row.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(row, text=self.format_addr(addr), text_color=COLORS["text"], font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(row=0, column=0, padx=12, pady=(10, 1), sticky="ew")
                ctk.CTkLabel(row, text="Đã kết nối", text_color=COLORS["success"], font=ctk.CTkFont(size=11), anchor="w").grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
                self.client_rows[addr] = row

        self.after(0, _refresh)

    def update_dashboard(self):
        active_transfers = sum(1 for state in self.transfer_states.values() if state == "Đang nhận")
        self.after(0, lambda: self.active_clients_value.configure(text=str(len(self.clients))))
        self.after(0, lambda: self.active_transfers_value.configure(text=str(active_transfers)))
        self.after(0, lambda: self.total_files_value.configure(text=str(self.total_files)))
        self.after(0, lambda: self.total_data_value.configure(text=self.format_bytes(self.total_bytes)))
        self.after(0, lambda: self.failed_value.configure(text=str(self.failed_uploads)))

    def update_uptime(self):
        if self.started_at and self.running:
            uptime = int(time.time() - self.started_at)
            self.uptime_value.configure(text=self.format_duration(uptime))
        elif not self.running:
            self.uptime_value.configure(text="--")
        self.after(1000, self.update_uptime)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"{timestamp} {level:<7} {message}\n"

        def _insert():
            self.log_area.configure(state="normal")
            try:
                self.log_area.insert("end", log_message, level)
            except TypeError:
                self.log_area.insert("end", log_message)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

        self.after(0, _insert)

    def clear_logs(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self.log("Đã xóa nhật ký.")

    def recv_exact(self, sock, size):
        chunks = []
        received = 0
        while received < size:
            chunk = sock.recv(size - received)
            if not chunk:
                raise ConnectionAbruptlyClosed("Kết nối bị đóng trước khi nhận đủ dữ liệu.")
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)

    def sanitize_subfolder(self, target_dir):
        cleaned = os.path.normpath(target_dir.strip()).replace("\\", os.sep).replace("/", os.sep)
        if cleaned in ("", "."):
            return ""
        parts = [part for part in cleaned.split(os.sep) if part and part not in (".", "..")]
        return os.path.join(*parts) if parts else ""

    def unique_file_path(self, folder, file_name):
        stem, ext = os.path.splitext(file_name)
        candidate = os.path.join(folder, file_name)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{stem} ({counter}){ext}")
            counter += 1
        return candidate

    def get_unblock_ip(self):
        ip = self.ip_entry.get().strip()
        return "127.0.0.1" if ip in ("0.0.0.0", "") else ip

    def format_addr(self, addr):
        return f"{addr[0]}:{addr[1]}"

    def format_bytes(self, value):
        value = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024

    def format_duration(self, seconds):
        if seconds < 60:
            return f"{seconds}s"
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"

    def on_closing(self):
        self.save_config()
        self.stop_server()
        self.destroy()


class ConnectionAbruptlyClosed(Exception):
    pass


if __name__ == "__main__":
    app = ServerApp()
    app.mainloop()
