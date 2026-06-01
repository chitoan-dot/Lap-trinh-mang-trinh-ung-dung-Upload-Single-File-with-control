import customtkinter as ctk
from tkinter import filedialog, messagebox
import socket
import threading
import os
import struct
import time
import json
import sys
from PIL import Image, ImageDraw

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "client_config.json")
SERVER_ERROR_OFFSET = (1 << 64) - 1
DUPLICATE_POLICIES = {
    "Tiếp tục nếu còn thiếu": "R",
    "Bỏ qua nếu đã có": "S",
    "Ghi đè": "O",
    "Đổi tên tự động": "N",
}
QUEUE_COLUMNS = (
    {"weight": 1, "minsize": 280},
    {"weight": 0, "minsize": 150},
    {"weight": 0, "minsize": 340},
    {"weight": 0, "minsize": 90},
    {"weight": 0, "minsize": 170},
)

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


if DND_AVAILABLE:
    class ClientBase(ctk.CTk, TkinterDnD.DnDWrapper):
        pass
else:
    ClientBase = ctk.CTk


class ClientApp(ClientBase):
    def __init__(self):
        super().__init__()

        # Cấu hình cửa sổ chính và theme cho giao diện client.
        self.title("Trình gửi tệp")
        self.geometry("1120x700")
        self.minsize(980, 640)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg"])

        # Các biến trạng thái dùng để quản lý hàng đợi và phiên upload hiện tại.
        self.file_paths = []
        self.upload_rows = {}
        self.file_states = {}
        self.upload_state = "stopped"
        self.upload_thread = None
        self.client_socket = None
        self.current_file = None
        self.completed_count = 0
        self.failed_count = 0
        self.total_uploaded_bytes = 0
        self.queue_total_bytes = 0
        self.queue_done_bytes = 0

        # Nạp icon cho các nút điều khiển, nếu thiếu file ảnh thì tự vẽ icon đơn giản.
        self.icons = {
            "start": self.make_icon("start"),
            "pause": self.make_icon("pause"),
            "resume": self.make_icon("resume"),
            "stop": self.make_icon("stop"),
            "browse": self.make_icon("browse"),
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Dựng các vùng giao diện chính.
        self.build_header()
        self.build_shell()
        self.build_toast()
        self.enable_drag_and_drop()

        self.load_config()
        self.update_ui_state()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_asset_path(self, asset_name):
        # Tìm đường dẫn asset, hỗ trợ cả khi đóng gói bằng PyInstaller.
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", asset_name)

    def make_icon(self, name):
        # Ưu tiên đọc icon PNG có sẵn; nếu không có thì vẽ icon bằng Pillow.
        path = self.get_asset_path(f"{name}.png")
        try:
            image = Image.open(path).convert("RGBA")
            if image.getbbox():
                return ctk.CTkImage(image, size=(18, 18))
        except Exception:
            pass

        image = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = (248, 250, 252, 255)
        if name == "start":
            draw.polygon([(8, 5), (19, 12), (8, 19)], fill=color)
        elif name == "pause":
            draw.rounded_rectangle((7, 5, 10, 19), radius=1, fill=color)
            draw.rounded_rectangle((14, 5, 17, 19), radius=1, fill=color)
        elif name == "resume":
            draw.polygon([(7, 5), (18, 12), (7, 19)], fill=color)
        elif name == "stop":
            draw.rounded_rectangle((6, 6, 18, 18), radius=2, fill=color)
        else:
            draw.rounded_rectangle((4, 8, 20, 18), radius=3, outline=color, width=2)
            draw.line((7, 8, 10, 5, 14, 5, 17, 8), fill=color, width=2)
        return ctk.CTkImage(image, size=(18, 18))

    def build_header(self):
        # Vùng tiêu đề trên cùng hiển thị tên app và trạng thái kết nối.
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=68)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        logo = ctk.CTkFrame(header, fg_color=COLORS["primary"], width=34, height=34, corner_radius=10)
        logo.grid(row=0, column=0, padx=(22, 12), pady=16)
        logo.grid_propagate(False)
        ctk.CTkLabel(logo, text="UP", font=ctk.CTkFont(size=12, weight="bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(title_box, text="Trình gửi tệp", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Quản lý hàng đợi, theo dõi tiến trình và tiếp tục gửi tệp", font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w")

        self.connection_pill = ctk.CTkLabel(
            header,
            text="CHƯA KẾT NỐI",
            width=128,
            fg_color=COLORS["surface_3"],
            text_color=COLORS["muted"],
            corner_radius=16,
            padx=14,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.connection_pill.grid(row=0, column=2, padx=22, pady=18, sticky="e")

    def build_shell(self):
        # Bố cục chính gồm sidebar cấu hình và khu vực bảng tiến trình.
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=1, column=0, padx=18, pady=18, sticky="nsew")
        shell.grid_columnconfigure(0, minsize=292)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(
            shell,
            fg_color=COLORS["surface"],
            corner_radius=16,
            scrollbar_button_color=COLORS["surface_3"],
            scrollbar_button_hover_color=COLORS["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(shell, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=2)
        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=4)

        self.build_sidebar()
        self.build_upload_card()
        self.build_progress_card()
        self.build_queue_table()
        self.build_controls()

    def build_sidebar(self):
        # Sidebar hiển thị thống kê nhanh và cấu hình server đích.
        ctk.CTkLabel(self.sidebar, text="Tổng quan", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"]).grid(row=0, column=0, padx=18, pady=(20, 12), sticky="w")

        self.speed_value = self.create_stat_card(self.sidebar, 1, "Tốc độ gửi", "0.00 MB/s")
        self.eta_value = self.create_stat_card(self.sidebar, 2, "ETA", "--")
        self.done_value = self.create_stat_card(self.sidebar, 3, "Hoàn tất", "0 tệp")
        self.failed_value = self.create_stat_card(self.sidebar, 4, "Lỗi", "0 tệp")

        settings = ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface_2"], corner_radius=14)
        settings.grid(row=5, column=0, padx=14, pady=(14, 16), sticky="ew")
        settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings, text="Máy chủ nhận tệp", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).grid(row=0, column=0, padx=14, pady=(14, 8), sticky="w")
        self.ip_entry = ctk.CTkEntry(settings, placeholder_text="127.0.0.1", height=36, fg_color=COLORS["surface"], border_color=COLORS["border"])
        self.ip_entry.grid(row=1, column=0, padx=14, pady=5, sticky="ew")
        self.port_entry = ctk.CTkEntry(settings, placeholder_text="8888", height=36, fg_color=COLORS["surface"], border_color=COLORS["border"])
        self.port_entry.grid(row=2, column=0, padx=14, pady=5, sticky="ew")
        self.server_folder_entry = ctk.CTkEntry(settings, placeholder_text="Thư mục lưu trên máy chủ", height=36, fg_color=COLORS["surface"], border_color=COLORS["border"])
        self.server_folder_entry.grid(row=3, column=0, padx=14, pady=5, sticky="ew")
        self.duplicate_policy_menu = ctk.CTkOptionMenu(
            settings,
            values=list(DUPLICATE_POLICIES.keys()),
            height=36,
            fg_color=COLORS["surface"],
            button_color=COLORS["surface_3"],
            button_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface_2"],
            dropdown_hover_color=COLORS["surface_3"],
            dropdown_text_color=COLORS["text"],
        )
        self.duplicate_policy_menu.grid(row=4, column=0, padx=14, pady=5, sticky="ew")
        self.duplicate_policy_menu.set("Tiếp tục nếu còn thiếu")

        self.save_settings_button = ctk.CTkButton(
            settings,
            text="Lưu cài đặt",
            command=self.save_config,
            height=36,
            fg_color=COLORS["surface_3"],
            hover_color=COLORS["border"],
            text_color=COLORS["button_text"],
            text_color_disabled=COLORS["button_disabled_text"],
        )
        self.save_settings_button.grid(row=5, column=0, padx=14, pady=(10, 14), sticky="ew")

    def create_stat_card(self, parent, row, label, value):
        # Tạo một ô thống kê nhỏ trong sidebar.
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface_2"], corner_radius=14)
        card.grid(row=row, column=0, padx=14, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"])
        value_label.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")
        return value_label

    def build_upload_card(self):
        # Khu vực chọn file hoặc kéo thả file vào hàng đợi.
        card = ctk.CTkFrame(self.main, fg_color=COLORS["surface"], corner_radius=16)
        card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        self.drop_card = ctk.CTkFrame(card, fg_color=COLORS["surface_2"], corner_radius=14, border_width=1, border_color=COLORS["border"], height=132)
        self.drop_card.grid(row=0, column=0, padx=14, pady=14, sticky="ew")
        self.drop_card.grid_columnconfigure(0, weight=1)
        self.drop_card.grid_propagate(False)
        self.drop_card.bind("<Button-1>", lambda _event: self.browse_files())

        ctk.CTkLabel(self.drop_card, text="Thêm tệp để gửi", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"], anchor="center").grid(row=0, column=0, padx=20, pady=(24, 4), sticky="ew")
        hint = "Kéo thả tệp vào cửa sổ hoặc bấm để chọn." if DND_AVAILABLE else "Bấm để chọn tệp. Có hỗ trợ chọn nhiều tệp."
        ctk.CTkLabel(self.drop_card, text=hint, font=ctk.CTkFont(size=12), text_color=COLORS["muted"], anchor="center").grid(row=1, column=0, padx=20, sticky="ew")

        browse = ctk.CTkButton(
            self.drop_card,
            text="Chọn tệp",
            image=self.icons["browse"],
            command=self.browse_files,
            height=34,
            width=132,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["button_text"],
            text_color_disabled=COLORS["button_disabled_text"],
        )
        browse.grid(row=2, column=0, padx=20, pady=(14, 20))
        self.browse_button = browse

    def build_progress_card(self):
        # Khu vực hiển thị tiến trình của file hiện tại và toàn bộ hàng đợi.
        card = ctk.CTkFrame(self.main, fg_color=COLORS["surface"], corner_radius=16)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self.current_file_label = ctk.CTkLabel(top, text="Chưa có tệp nào đang gửi", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"], anchor="w")
        self.current_file_label.grid(row=0, column=0, sticky="ew")
        self.state_chip = ctk.CTkLabel(top, text="SẴN SÀNG", width=112, fg_color=COLORS["surface_3"], text_color=COLORS["muted"], corner_radius=14, padx=12, height=28, font=ctk.CTkFont(size=11, weight="bold"))
        self.state_chip.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(card, height=14, fg_color=COLORS["surface_3"], progress_color=COLORS["primary"], corner_radius=8)
        self.progress_bar.grid(row=1, column=0, padx=16, pady=(2, 5), sticky="ew")
        self.progress_bar.set(0)

        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        meta.grid_columnconfigure((0, 1, 2), weight=1)
        self.progress_label = ctk.CTkLabel(meta, text="0.00% | 0 B / 0 B", text_color=COLORS["muted"], anchor="w")
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.speed_label = ctk.CTkLabel(meta, text="Tốc độ: 0.00 MB/s", text_color=COLORS["muted"])
        self.speed_label.grid(row=0, column=1)
        self.eta_label = ctk.CTkLabel(meta, text="ETA: --", text_color=COLORS["muted"], anchor="e")
        self.eta_label.grid(row=0, column=2, sticky="e")
        self.total_progress_bar = ctk.CTkProgressBar(card, height=8, fg_color=COLORS["surface_3"], progress_color=COLORS["success"], corner_radius=6)
        self.total_progress_bar.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="ew")
        self.total_progress_bar.set(0)
        self.total_progress_label = ctk.CTkLabel(card, text="Tổng: 0.00% | 0 B / 0 B", text_color=COLORS["subtle"], anchor="w", font=ctk.CTkFont(size=11))
        self.total_progress_label.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

    def build_queue_table(self):
        # Bảng hàng đợi hiển thị từng file, dung lượng, tiến trình, ETA và trạng thái.
        table = ctk.CTkFrame(self.main, fg_color=COLORS["surface"], corner_radius=16)
        self.queue_table = table
        table.grid(row=1, column=0, columnspan=2, pady=(12, 0), sticky="nsew")
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(1, weight=0)
        table.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(table, fg_color="transparent")
        toolbar.grid(row=0, column=0, padx=18, pady=(16, 10), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(toolbar, text="Hàng đợi gửi tệp", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        self.retry_button = ctk.CTkButton(toolbar, text="Gửi lại lỗi", width=126, height=32, command=self.retry_failed, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.retry_button.grid(row=0, column=1, padx=(0, 8), sticky="e")
        self.clear_button = ctk.CTkButton(toolbar, text="Xóa mục xong", width=150, height=32, command=self.clear_completed, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.clear_button.grid(row=0, column=2, sticky="e")

        header = ctk.CTkFrame(table, fg_color=COLORS["surface_2"], corner_radius=8)
        header.grid(row=1, column=0, padx=18, pady=(0, 8), sticky="ew")
        header.grid_propagate(False)
        header.configure(height=46)
        self.configure_queue_columns(header)
        header.grid_rowconfigure(0, weight=1)
        header_specs = (
            ("Tệp", "w"),
            ("Dung lượng", "center"),
            ("Tiến trình", "center"),
            ("ETA", "center"),
            ("Trạng thái", "center"),
        )
        for column, (text, anchor) in enumerate(header_specs):
            ctk.CTkLabel(header, text=text, text_color=COLORS["muted"], font=ctk.CTkFont(size=11, weight="bold"), anchor=anchor).grid(row=0, column=column, padx=12, sticky="nsew")

        self.queue_frame = ctk.CTkScrollableFrame(table, fg_color="transparent")
        self.queue_frame.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        self.empty_queue = ctk.CTkLabel(self.queue_frame, text="Chưa chọn tệp nào.", text_color=COLORS["subtle"])
        self.empty_queue.grid(row=0, column=0, pady=30)

    def configure_queue_columns(self, container):
        # Dùng chung cấu hình cột để header và từng dòng file thẳng hàng nhau.
        for index, options in enumerate(QUEUE_COLUMNS):
            container.grid_columnconfigure(index, weight=options["weight"], minsize=options["minsize"])

    def build_controls(self):
        # Thanh điều khiển dưới cùng: bắt đầu, tạm dừng/tiếp tục và dừng.
        controls = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=70)
        controls.grid(row=2, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)
        controls.grid_propagate(False)

        inner = ctk.CTkFrame(controls, fg_color="transparent")
        inner.grid(row=0, column=1, padx=18, pady=14, sticky="e")

        self.status_label = ctk.CTkLabel(controls, text="Sẵn sàng. Thêm tệp và bắt đầu gửi.", text_color=COLORS["muted"], anchor="w")
        self.status_label.grid(row=0, column=0, padx=22, pady=22, sticky="w")

        self.start_button = ctk.CTkButton(inner, text="Bắt đầu gửi", image=self.icons["start"], command=self.start_upload, height=40, width=140, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"])
        self.start_button.grid(row=0, column=0, padx=5)
        self.pause_resume_button = ctk.CTkButton(inner, text="Tạm dừng", image=self.icons["pause"], command=self.pause_resume_upload, height=40, width=140, fg_color=COLORS["surface_3"], hover_color=COLORS["border"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"], state=ctk.DISABLED)
        self.pause_resume_button.grid(row=0, column=1, padx=5)
        self.stop_button = ctk.CTkButton(inner, text="Dừng", image=self.icons["stop"], command=self.stop_upload, height=40, width=110, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color=COLORS["button_text"], text_color_disabled=COLORS["button_disabled_text"], state=ctk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)

    def build_toast(self):
        # Toast là thông báo nhỏ hiện tạm thời ở góc giao diện.
        self.toast = ctk.CTkLabel(
            self,
            text="",
            fg_color=COLORS["surface_3"],
            text_color=COLORS["text"],
            corner_radius=12,
            padx=16,
            height=40,
        )

    def enable_drag_and_drop(self):
        # Bật kéo thả file nếu thư viện tkinterdnd2 khả dụng.
        if not DND_AVAILABLE:
            return
        try:
            self.TkdndVersion = TkinterDnD._require(self)
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self.handle_drop)
        except Exception:
            pass

    def handle_drop(self, event):
        # Nhận danh sách file được thả vào cửa sổ và thêm vào hàng đợi.
        files = self.tk.splitlist(event.data)
        self.add_files(files)

    def show_toast(self, message, kind="info"):
        # Hiển thị thông báo nhanh với màu theo loại: success, warning, error, info.
        color = {
            "info": COLORS["surface_3"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"],
        }.get(kind, COLORS["surface_3"])

        def _show():
            self.toast.configure(text=message, fg_color=color)
            self.toast.place(relx=1.0, rely=0.0, x=-22, y=84, anchor="ne")
            self.after(3200, self.toast.place_forget)

        self.after(0, _show)

    def browse_files(self):
        # Mở hộp thoại chọn một hoặc nhiều file từ máy người dùng.
        files = filedialog.askopenfilenames(parent=self)
        if files:
            self.add_files(files)

    def add_files(self, files):
        # Thêm file hợp lệ vào hàng đợi, bỏ qua file trùng hoặc không tồn tại.
        added = 0
        duplicates = 0
        for path in files:
            normalized = os.path.abspath(path)
            if not os.path.isfile(normalized):
                continue
            if normalized in self.file_paths:
                duplicates += 1
                continue
            self.file_paths.append(normalized)
            self.add_queue_row(normalized)
            added += 1
        if added:
            self.status_label.configure(text=f"Đã thêm {added} tệp vào hàng đợi.")
            self.show_toast(f"Đã thêm {added} tệp", "success")
            self.update_ui_state()
        if duplicates:
            message = "Tệp đã có trong hàng đợi." if duplicates == 1 else f"{duplicates} tệp đã có trong hàng đợi."
            self.status_label.configure(text=message)
            self.show_toast(message, "warning")

    def add_queue_row(self, path):
        # Tạo một dòng giao diện tương ứng với file vừa được thêm vào hàng đợi.
        if self.empty_queue.winfo_exists():
            self.empty_queue.grid_forget()

        row_index = len(self.upload_rows)
        row = ctk.CTkFrame(self.queue_frame, fg_color=COLORS["surface_2"], corner_radius=10, height=58)
        row.grid(row=row_index, column=0, pady=5, sticky="ew")
        row.grid_propagate(False)
        self.configure_queue_columns(row)
        row.grid_rowconfigure(0, weight=1)

        name = os.path.basename(path)
        size = os.path.getsize(path)
        name_label = ctk.CTkLabel(row, text=name, text_color=COLORS["text"], anchor="w")
        name_label.grid(row=0, column=0, padx=(14, 12), sticky="nsew")
        size_label = ctk.CTkLabel(row, text=self.format_bytes(size), text_color=COLORS["muted"], anchor="center")
        size_label.grid(row=0, column=1, padx=12, sticky="nsew")
        progress = ctk.CTkProgressBar(row, height=10, fg_color=COLORS["surface_3"], progress_color=COLORS["primary"], corner_radius=6)
        progress.grid(row=0, column=2, padx=18, sticky="ew")
        progress.set(0)
        eta = ctk.CTkLabel(row, text="--", text_color=COLORS["muted"], anchor="center")
        eta.grid(row=0, column=3, padx=12, sticky="nsew")
        state = ctk.CTkLabel(row, text="Đang chờ", width=118, text_color=COLORS["muted"], fg_color=COLORS["surface_3"], corner_radius=12, padx=10, height=28)
        state.grid(row=0, column=4, padx=(12, 14), sticky="")

        self.upload_rows[path] = {
            "row": row,
            "name": name_label,
            "size": size_label,
            "progress": progress,
            "eta": eta,
            "state": state,
        }
        self.file_states[path] = "Đang chờ"

    def clear_completed(self):
        # Xóa khỏi bảng các file đã hoàn tất, lỗi hoặc đã bỏ qua.
        for path, widgets in list(self.upload_rows.items()):
            state = self.file_states.get(path, widgets["state"].cget("text"))
            if state in ("Hoàn tất", "Lỗi", "Đã bỏ qua"):
                widgets["row"].destroy()
                del self.upload_rows[path]
                self.file_states.pop(path, None)
                if path in self.file_paths:
                    self.file_paths.remove(path)
        if not self.upload_rows:
            self.empty_queue.grid(row=0, column=0, pady=30)
        self.status_label.configure(text="Đã xóa các mục hoàn tất.")

    def retry_failed(self):
        # Đưa các file lỗi/dừng về trạng thái chờ để gửi lại.
        if self.upload_state != "stopped":
            return
        retry_paths = [path for path in self.file_paths if self.file_states.get(path) in ("Lỗi", "Đã dừng")]
        if not retry_paths:
            self.show_toast("Không có tệp lỗi để gửi lại", "info")
            return
        for path in retry_paths:
            self.update_row(path, progress=0, eta="--", state="Đang chờ", state_color=COLORS["surface_3"])
        self.refresh_stats()
        self.start_upload()

    def update_row(self, path, progress=None, eta=None, state=None, state_color=None):
        # Cập nhật một dòng trong bảng hàng đợi từ thread upload thông qua after().
        if path not in self.upload_rows:
            return
        if state is not None:
            self.file_states[path] = state

        def _update():
            widgets = self.upload_rows.get(path)
            if not widgets:
                return
            if progress is not None:
                widgets["progress"].set(progress)
            if eta is not None:
                widgets["eta"].configure(text=eta)
            if state is not None:
                widgets["state"].configure(text=state, text_color=COLORS["text"], fg_color=state_color or COLORS["surface_3"])

        self.after(0, _update)

    def reset_progress(self):
        # Đưa các thanh tiến trình và nhãn thống kê về trạng thái ban đầu.
        self.progress_bar.set(0)
        self.progress_label.configure(text="0.00% | 0 B / 0 B")
        self.speed_label.configure(text="Tốc độ: 0.00 MB/s")
        self.eta_label.configure(text="ETA: --")
        self.speed_value.configure(text="0.00 MB/s")
        self.eta_value.configure(text="--")
        self.current_file_label.configure(text="Chưa có tệp nào đang gửi")
        self.total_progress_bar.set(0)
        self.total_progress_label.configure(text="Tổng: 0.00% | 0 B / 0 B")

    def update_ui_state(self):
        # Bật/tắt các nút dựa trên trạng thái hiện tại của phiên upload.
        has_files = bool(self.file_paths)
        if self.upload_state == "stopped":
            self.start_button.configure(state=ctk.NORMAL if has_files else ctk.DISABLED)
            self.pause_resume_button.configure(state=ctk.DISABLED, text="Tạm dừng", image=self.icons["pause"])
            self.stop_button.configure(state=ctk.DISABLED)
            self.browse_button.configure(state=ctk.NORMAL)
            self.save_settings_button.configure(state=ctk.NORMAL)
            self.retry_button.configure(state=ctk.NORMAL)
            self.state_chip.configure(text="SẴN SÀNG", fg_color=COLORS["surface_3"], text_color=COLORS["muted"])
            self.connection_pill.configure(text="CHƯA KẾT NỐI", fg_color=COLORS["surface_3"], text_color=COLORS["muted"])
        elif self.upload_state == "uploading":
            self.start_button.configure(state=ctk.DISABLED)
            self.pause_resume_button.configure(state=ctk.NORMAL, text="Tạm dừng", image=self.icons["pause"])
            self.stop_button.configure(state=ctk.NORMAL)
            self.browse_button.configure(state=ctk.DISABLED)
            self.save_settings_button.configure(state=ctk.DISABLED)
            self.retry_button.configure(state=ctk.DISABLED)
            self.state_chip.configure(text="ĐANG GỬI", fg_color=COLORS["primary"], text_color="white")
            self.connection_pill.configure(text="ĐÃ KẾT NỐI", fg_color=COLORS["success"], text_color="white")
        elif self.upload_state == "paused":
            self.start_button.configure(state=ctk.DISABLED)
            self.pause_resume_button.configure(state=ctk.NORMAL, text="Tiếp tục", image=self.icons["resume"])
            self.stop_button.configure(state=ctk.NORMAL)
            self.retry_button.configure(state=ctk.DISABLED)
            self.state_chip.configure(text="TẠM DỪNG", fg_color=COLORS["warning"], text_color=COLORS["bg"])

    def start_upload(self):
        # Kiểm tra dữ liệu nhập và tạo thread nền để không làm treo giao diện.
        if not self.file_paths:
            messagebox.showerror("Chưa có tệp", "Vui lòng thêm ít nhất một tệp.", parent=self)
            return
        try:
            int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Port không hợp lệ", "Port máy chủ phải là số.", parent=self)
            return

        self.upload_state = "uploading"
        self.update_ui_state()
        self.upload_thread = threading.Thread(target=self.upload_queue_thread, daemon=True)
        self.upload_thread.start()

    def pause_resume_upload(self):
        # Chuyển qua lại giữa trạng thái đang gửi và tạm dừng.
        if self.upload_state == "uploading":
            self.upload_state = "paused"
            self.status_label.configure(text="Đã tạm dừng gửi tệp.")
            self.show_toast("Đã tạm dừng gửi tệp", "warning")
        elif self.upload_state == "paused":
            self.upload_state = "uploading"
            self.status_label.configure(text="Đang tiếp tục gửi tệp...")
            self.show_toast("Đang tiếp tục gửi tệp", "info")
        self.update_ui_state()

    def stop_upload(self):
        # Dừng phiên gửi hiện tại và đóng socket để server ngừng nhận file.
        if self.upload_state in ("uploading", "paused"):
            self.upload_state = "stopped"
            if self.client_socket:
                try:
                    self.client_socket.close()
                except Exception:
                    pass
            self.status_label.configure(text="Người dùng đã dừng phiên gửi.")
            self.show_toast("Đã dừng phiên gửi", "warning")
            self.update_ui_state()

    def on_closing(self):
        # Khi đóng cửa sổ, dừng upload và lưu lại cấu hình hiện tại.
        self.stop_upload()
        self.save_config(silent=True)
        self.destroy()

    def save_config(self, silent=False):
        # Lưu cấu hình client vào file JSON để lần sau mở app dùng lại.
        config = {
            "server_ip": self.ip_entry.get(),
            "server_port": self.port_entry.get(),
            "server_folder": self.server_folder_entry.get(),
            "duplicate_policy": self.duplicate_policy_menu.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            if not silent:
                self.status_label.configure(text="Đã lưu cài đặt.")
                self.show_toast("Đã lưu cài đặt", "success")
        except Exception as e:
            self.status_label.configure(text=f"Lỗi khi lưu cài đặt: {e}")

    def load_config(self):
        # Đọc cấu hình client từ JSON; nếu chưa có thì dùng giá trị mặc định.
        defaults = {"server_ip": "127.0.0.1", "server_port": "8888", "server_folder": "", "duplicate_policy": "Tiếp tục nếu còn thiếu"}
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
        except Exception as e:
            self.status_label.configure(text=f"Lỗi khi tải cài đặt: {e}")

        self.ip_entry.insert(0, defaults["server_ip"])
        self.port_entry.insert(0, defaults["server_port"])
        self.server_folder_entry.insert(0, defaults["server_folder"])
        self.duplicate_policy_menu.set(defaults.get("duplicate_policy", "Tiếp tục nếu còn thiếu"))

    def upload_queue_thread(self):
        # Thread nền duyệt lần lượt các file chưa hoàn tất trong hàng đợi.
        pending_paths = [path for path in self.file_paths if self.file_states.get(path) not in ("Hoàn tất", "Đã bỏ qua")]
        self.queue_total_bytes = sum(os.path.getsize(path) for path in pending_paths if os.path.exists(path))
        self.queue_done_bytes = 0
        self.update_total_progress(0)

        for path in pending_paths:
            # Nếu người dùng bấm Stop thì dừng duyệt hàng đợi.
            if self.upload_state == "stopped":
                break
            current_state = self.file_states.get(path)
            if current_state in ("Hoàn tất", "Đã bỏ qua"):
                continue
            self.current_file = path
            self.upload_single_file(path)

        if self.upload_state != "stopped":
            self.upload_state = "stopped"
            self.after(0, self.update_ui_state)
            self.after(0, lambda: self.status_label.configure(text="Đã gửi xong hàng đợi."))
            self.show_toast("Đã gửi xong hàng đợi", "success")

    def update_total_progress(self, current_file_bytes=0):
        # Cập nhật thanh tiến trình tổng bằng số byte đã xong cộng với file đang gửi.
        total_done = min(self.queue_done_bytes + current_file_bytes, self.queue_total_bytes)
        progress = total_done / self.queue_total_bytes if self.queue_total_bytes else 0
        text = f"Tổng: {progress:.2%} | {self.format_bytes(total_done)} / {self.format_bytes(self.queue_total_bytes)}"
        self.after(0, lambda p=progress: self.total_progress_bar.set(p))
        self.after(0, lambda value=text: self.total_progress_label.configure(text=value))

    def upload_single_file(self, file_path):
        # Gửi một file duy nhất tới server theo cấu hình hiện tại.
        server_ip = self.ip_entry.get()
        server_port = int(self.port_entry.get())
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        target_dir = self.server_folder_entry.get().strip()
        duplicate_policy = DUPLICATE_POLICIES.get(self.duplicate_policy_menu.get(), "R")

        self.after(0, lambda: self.current_file_label.configure(text=file_name))
        self.update_row(file_path, state="Đang kết nối", state_color=COLORS["warning"])

        try:
            # Mở kết nối TCP tới server.
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.after(0, lambda: self.status_label.configure(text=f"Đang gửi {file_name} tới {server_ip}:{server_port}"))
            self.update_row(file_path, state="Đang gửi", state_color=COLORS["primary"])

            self.client_socket.sendall(b"U")

            # Gửi header gồm thư mục đích, tên file, kích thước và duplicate policy.
            dir_name_bytes = target_dir.encode()
            self.client_socket.sendall(struct.pack("!I", len(dir_name_bytes)))
            self.client_socket.sendall(dir_name_bytes)

            file_name_bytes = file_name.encode()
            self.client_socket.sendall(struct.pack("!I", len(file_name_bytes)))
            self.client_socket.sendall(file_name_bytes)
            self.client_socket.sendall(struct.pack("!Q", file_size))
            self.client_socket.sendall(duplicate_policy.encode())

            # Server trả offset để client biết gửi từ đầu, gửi tiếp, hoặc bỏ qua.
            offset_data = self.recv_exact(self.client_socket, 8)
            offset = struct.unpack("!Q", offset_data)[0]
            if offset == SERVER_ERROR_OFFSET:
                raise RuntimeError("Máy chủ không đủ dung lượng để nhận tệp này.")

            if offset >= file_size:
                self.completed_count += 1
                self.update_row(file_path, progress=1, eta="0s", state="Đã bỏ qua", state_color=COLORS["success"])
                self.queue_done_bytes += file_size
                self.update_total_progress(0)
                self.refresh_stats()
                return

            # Mở file local và gửi dữ liệu từ offset đã nhận.
            with open(file_path, "rb") as f:
                f.seek(offset)
                sent_bytes = offset
                last_update_time = time.time()
                last_sample_bytes = sent_bytes
                speed_mb = 0.0

                while sent_bytes < file_size and self.upload_state != "stopped":
                    # Khi tạm dừng, giữ kết nối nhưng chưa đọc/gửi chunk tiếp theo.
                    while self.upload_state == "paused":
                        self.update_row(file_path, state="Tạm dừng", state_color=COLORS["warning"])
                        time.sleep(0.1)
                        last_update_time = time.time()
                        last_sample_bytes = sent_bytes
                        if self.upload_state == "stopped":
                            break
                    if self.upload_state == "stopped":
                        break

                    data = f.read(65536)
                    if not data:
                        break

                    # Gửi chunk dữ liệu qua socket.
                    self.client_socket.sendall(data)
                    sent_bytes += len(data)
                    self.total_uploaded_bytes += len(data)

                    # Giới hạn tần suất cập nhật UI để giao diện không bị quá tải.
                    now = time.time()
                    elapsed = now - last_update_time
                    if elapsed >= 0.35 or sent_bytes == file_size:
                        bytes_delta = sent_bytes - last_sample_bytes
                        instant_speed = bytes_delta / elapsed if elapsed > 0 else 0
                        speed_mb = instant_speed / (1024 * 1024)
                        remaining = max(file_size - sent_bytes, 0)
                        eta_seconds = int(remaining / instant_speed) if instant_speed > 0 else None
                        progress = sent_bytes / file_size if file_size else 1
                        eta_text = self.format_duration(eta_seconds)
                        progress_text = f"{progress:.2%} | {self.format_bytes(sent_bytes)} / {self.format_bytes(file_size)}"

                        self.after(0, lambda p=progress: self.progress_bar.set(p))
                        self.after(0, lambda text=progress_text: self.progress_label.configure(text=text))
                        self.after(0, lambda s=speed_mb: self.speed_label.configure(text=f"Tốc độ: {s:.2f} MB/s"))
                        self.after(0, lambda e=eta_text: self.eta_label.configure(text=f"ETA: {e}"))
                        self.after(0, lambda s=speed_mb: self.speed_value.configure(text=f"{s:.2f} MB/s"))
                        self.after(0, lambda e=eta_text: self.eta_value.configure(text=e))
                        self.update_total_progress(sent_bytes)
                        self.update_row(file_path, progress=progress, eta=eta_text, state="Đang gửi", state_color=COLORS["primary"])

                        last_update_time = now
                        last_sample_bytes = sent_bytes

            if self.upload_state == "stopped":
                self.update_row(file_path, state="Đã dừng", state_color=COLORS["warning"])
            else:
                self.completed_count += 1
                self.update_row(file_path, progress=1, eta="0s", state="Hoàn tất", state_color=COLORS["success"])
                self.queue_done_bytes += file_size
                self.update_total_progress(0)
                self.after(0, lambda: self.status_label.configure(text=f"Hoàn tất: {file_name}"))
                self.show_toast(f"Đã gửi xong {file_name}", "success")

        except (ConnectionRefusedError, socket.gaierror):
            # Trường hợp không kết nối được tới server hoặc sai địa chỉ.
            self.failed_count += 1
            self.update_row(file_path, state="Lỗi", state_color=COLORS["danger"])
            self.show_toast("Kết nối thất bại", "error")
            self.after(0, lambda: messagebox.showerror("Lỗi kết nối", f"Không thể kết nối tới {server_ip}:{server_port}.", parent=self))
            self.upload_state = "stopped"
        except Exception as e:
            # Các lỗi còn lại khi gửi file: mất kết nối, lỗi đọc file, lỗi protocol...
            if self.upload_state != "stopped":
                self.failed_count += 1
                self.update_row(file_path, state="Lỗi", state_color=COLORS["danger"])
                self.show_toast("Gửi tệp thất bại", "error")
                self.after(0, lambda err=e: messagebox.showerror("Lỗi gửi tệp", f"Đã xảy ra lỗi: {err}", parent=self))
                self.upload_state = "stopped"
        finally:
            # Luôn đóng socket sau khi xử lý xong file để tránh rò rỉ kết nối.
            if self.client_socket:
                try:
                    self.client_socket.close()
                except Exception:
                    pass
                self.client_socket = None
            self.refresh_stats()
            if self.upload_state == "stopped":
                self.after(0, self.update_ui_state)

    def recv_exact(self, sock, size):
        # Đọc đúng số byte từ server, dùng khi nhận offset hoặc dữ liệu protocol.
        chunks = []
        received = 0
        while received < size:
            chunk = sock.recv(size - received)
            if not chunk:
                raise ConnectionError("Kết nối bị đóng khi đang đọc dữ liệu từ server.")
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)

    def refresh_stats(self):
        # Đếm lại số file hoàn tất và lỗi để cập nhật sidebar.
        done = sum(1 for state in self.file_states.values() if state in ("Hoàn tất", "Đã bỏ qua"))
        failed = sum(1 for state in self.file_states.values() if state == "Lỗi")
        self.after(0, lambda: self.done_value.configure(text=f"{done} tệp"))
        self.after(0, lambda: self.failed_value.configure(text=f"{failed} tệp"))

    def format_bytes(self, value):
        # Định dạng dung lượng byte thành chuỗi dễ đọc.
        value = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024

    def format_duration(self, seconds):
        # Định dạng thời gian còn lại cho cột ETA.
        if seconds is None:
            return "--"
        if seconds < 60:
            return f"{seconds}s"
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"


