import os
import socket
import threading
import struct
import time
import hashlib
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *

from common.constants import (
    CHUNK_SIZE,
    DEFAULT_BIND_HOST,
    DEFAULT_PORT,
    SERVER_VERIFY_FAILED,
    SERVER_VERIFY_OK,
    SERVER_VERIFY_SKIPPED,
)
from layout.theme import *


HASH_CHUNK_SIZE = 1024 * 1024
TRANSFER_UPDATE_INTERVAL = 0.25
SOCKET_BACKLOG = 10


class ServerMonitorUI(QWidget):
    log_signal = pyqtSignal(str)
    stat_signal = pyqtSignal()
    transfer_signal = pyqtSignal(str, str, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPLOWER - Giám sát Server")
        self.resize(1450, 840)
        self.setMinimumSize(1100, 720)

        self.host = DEFAULT_BIND_HOST
        self.port = DEFAULT_PORT
        self.upload_dir = os.path.abspath("Uploads")

        self.server_socket = None
        self.running = False
        self.listen_thread = None

        self.clients = {}
        self.transfer_rows = {}
        self.transfer_paths = {}

        self.total_files = 0
        self.total_bytes = 0
        self.failed_count = 0
        self.active_transfers = 0
        self.started_at = None

        self.setStyleSheet(self.page_style())
        self.build_ui()

        self.log_signal.connect(self.add_log)
        self.stat_signal.connect(self.update_stats)
        self.transfer_signal.connect(self.update_transfer_row)

    def page_style(self):
        return f"""
        QWidget {{
            background:{BG};
            color:{TEXT};
            font-family:Segoe UI, Arial;
            font-size:15px;
        }}

        QLabel {{
            border:none;
            background:transparent;
        }}

        QPushButton {{
            border:none;
        }}

        QLineEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:16px;
            font-size:16px;
        }}

        QFrame#Card {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}

        QFrame#Card:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}

        QFrame#StatCard {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}

        QFrame#StatCard:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}

        QFrame#Plain {{
            background:transparent;
            border:none;
        }}

        QTableWidget {{
            background:{CARD};
            color:{TEXT};
            border:1px solid {BORDER};
            border-radius:18px;
            gridline-color:transparent;
        }}

        QHeaderView::section {{
            background:#13162a;
            color:{TEXT2};
            border:none;
            padding:12px;
            font-size:16px;
            font-weight:bold;
        }}

        QTableWidget::item {{
            border:none;
            padding:8px;
        }}

        QTableWidget::item:hover {{
            background:#1f1238;
            color:white;
        }}

        QTableWidget::item:selected {{
            background:#30174f;
            color:white;
        }}

        QTextEdit {{
            background:{CARD};
            color:{TEXT2};
            border:1px solid {BORDER};
            border-radius:18px;
            padding:12px;
            font-family:Consolas;
        }}

        QTabWidget::pane {{
            border:1px solid {BORDER};
            border-radius:18px;
            background:{CARD};
        }}

        QTabBar::tab {{
            background:{CARD2};
            color:{TEXT2};
            padding:12px 28px;
            border:none;
        }}

        QTabBar::tab:selected {{
            background:#30174f;
            color:#d18cff;
        }}
        """

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 35, 40, 35)
        root.setSpacing(26)

        top = QHBoxLayout()
        top.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title = QLabel("Máy Chủ Nhận Tệp")
        title.setWordWrap(True)
        title.setMinimumWidth(360)
        title.setStyleSheet("""
        QLabel {
            font-size:32px;
            font-weight:900;
            color:white;
            border:none;
            background:transparent;
        }
        """)

        subtitle = QLabel("Bật server, theo dõi thiết bị gửi và phiên nhận file")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
        QLabel {{
            font-size:16px;
            color:{TEXT2};
            border:none;
            background:transparent;
        }}
        """)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.host_input = QLineEdit(self.host)
        self.host_input.setFixedSize(126, 48)

        self.port_input = QLineEdit(str(self.port))
        self.port_input.setFixedSize(90, 48)

        self.status_label = QLabel("ĐÃ DỪNG")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedSize(104, 48)
        self.status_label.setStyleSheet("""
        QLabel {
            background:#831843;
            color:white;
            border:none;
            border-radius:14px;
            font-weight:900;
        }
        """)

        self.start_btn = QPushButton("Bắt đầu")
        self.start_btn.setFixedSize(104, 48)
        self.start_btn.setStyleSheet(self.primary_button_style())
        self.start_btn.clicked.connect(self.start_server)

        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setFixedSize(92, 48)
        self.stop_btn.setStyleSheet(self.danger_button_style())
        self.stop_btn.clicked.connect(self.stop_server)

        top.addLayout(title_box, 1)
        top.addWidget(self.host_input)
        top.addWidget(self.port_input)
        top.addWidget(self.status_label)
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)

        root.addLayout(top)

        stats = QHBoxLayout()
        stats.setSpacing(20)

        self.lbl_clients = self.stat_card("Thiết bị gửi", "0")
        self.lbl_transfers = self.stat_card("Đang nhận", "0")
        self.lbl_files = self.stat_card("Tệp đã nhận", "0")
        self.lbl_data = self.stat_card("Dữ liệu", "0 B")
        self.lbl_errors = self.stat_card("Lỗi", "0")
        self.lbl_time = self.stat_card("Thời gian", "--")

        for w in [
            self.lbl_clients,
            self.lbl_transfers,
            self.lbl_files,
            self.lbl_data,
            self.lbl_errors,
            self.lbl_time,
        ]:
            stats.addWidget(w)

        root.addLayout(stats)

        storage = QFrame()
        storage.setObjectName("Card")

        storage_layout = QVBoxLayout(storage)
        storage_layout.setContentsMargins(24, 22, 24, 22)
        storage_layout.setSpacing(14)

        storage_title = QLabel("Thư mục lưu tệp")
        storage_title.setStyleSheet(f"""
        QLabel {{
            font-size:20px;
            font-weight:900;
            color:{TEXT};
            border:none;
            background:transparent;
        }}
        """)

        folder_row = QHBoxLayout()

        self.folder_input = QLineEdit(self.upload_dir)
        self.folder_input.setFixedHeight(52)

        choose_btn = QPushButton("Chọn")
        choose_btn.setFixedSize(100, 52)
        choose_btn.setStyleSheet(self.control_button_style())
        choose_btn.clicked.connect(self.choose_folder)

        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(choose_btn)

        self.lan_label = QLabel(f"Địa chỉ LAN: {self.get_lan_ip()}:{self.port}")
        self.lan_label.setStyleSheet(f"""
        QLabel {{
            color:{TEXT2};
            font-size:15px;
            border:none;
            background:transparent;
        }}
        """)

        storage_layout.addWidget(storage_title)
        storage_layout.addLayout(folder_row)
        storage_layout.addWidget(self.lan_label)

        root.addWidget(storage)

        self.tabs = QTabWidget()

        self.transfer_table = QTableWidget()
        self.transfer_table.setColumnCount(6)
        self.transfer_table.setHorizontalHeaderLabels(
            ["Tệp", "Thiết bị gửi", "Tiến trình", "Tốc độ", "Trạng thái", "Mở"]
        )
        self.transfer_table.verticalHeader().setVisible(False)
        self.transfer_table.setShowGrid(False)
        self.transfer_table.horizontalHeader().setStretchLastSection(True)
        self.transfer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.tabs.addTab(self.transfer_table, "Phiên nhận")
        self.tabs.addTab(self.log_box, "Nhật ký")

        root.addWidget(self.tabs, 1)

        self.update_buttons()
        self.log_signal.emit("Màn hình Server sẵn sàng.")

    def stat_card(self, name, value):
        card = QFrame()
        card.setObjectName("StatCard")
        card.setMinimumHeight(120)

        box = QVBoxLayout(card)
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(8)

        title = QLabel(name)
        title.setStyleSheet(f"""
        QLabel {{
            color:{TEXT2};
            font-size:15px;
            border:none;
            background:transparent;
        }}
        """)

        val = QLabel(value)
        val.setStyleSheet("""
        QLabel {
            color:white;
            font-size:26px;
            font-weight:900;
            border:none;
            background:transparent;
        }
        """)

        box.addWidget(title)
        box.addStretch()
        box.addWidget(val)

        card.value_label = val
        return card

    def primary_button_style(self):
        return f"""
        QPushButton {{
            background:{GRADIENT};
            color:white;
            border:none;
            border-radius:14px;
            font-size:17px;
            font-weight:900;
        }}
        QPushButton:hover {{
            background:#ec4899;
        }}
        QPushButton:pressed {{
            background:#c026d3;
        }}
        """

    def danger_button_style(self):
        return """
        QPushButton {
            background:#ff4d5a;
            color:white;
            border:none;
            border-radius:14px;
            font-size:17px;
            font-weight:900;
        }
        QPushButton:hover {
            background:#dc2626;
        }
        QPushButton:pressed {
            background:#b91c1c;
        }
        """

    def control_button_style(self):
        return f"""
        QPushButton {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:14px;
            font-size:17px;
            font-weight:900;
        }}
        QPushButton:hover {{
            border:1px solid {PRIMARY};
            background:#171832;
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        """

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file")
        if folder:
            self.upload_dir = folder
            self.folder_input.setText(folder)
            self.log_signal.emit(f"Đã chọn thư mục lưu: {folder}")

    def server_address(self):
        return f"{self.host}:{self.port}"

    def create_server_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(SOCKET_BACKLOG)
        return server_socket

    def start_server(self):
        if self.running:
            return

        try:
            self.host = self.host_input.text().strip() or DEFAULT_BIND_HOST
            self.port = int(self.port_input.text().strip() or str(DEFAULT_PORT))
            self.upload_dir = self.folder_input.text().strip() or os.path.abspath("Uploads")
            os.makedirs(self.upload_dir, exist_ok=True)

            self.server_socket = self.create_server_socket()

            self.running = True
            self.started_at = time.time()

            self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)
            self.listen_thread.start()

            self.status_label.setText("ĐANG CHẠY")
            self.status_label.setStyleSheet("""
            QLabel {
                background:#064e3b;
                color:#00ff88;
                border:none;
                border-radius:14px;
                font-weight:900;
            }
            """)

            self.lan_label.setText(f"Địa chỉ LAN: {self.get_lan_ip()}:{self.port}")
            self.log_signal.emit(f"Server đang chạy tại {self.server_address()}")

        except Exception as e:
            self.running = False
            self.log_signal.emit(f"Lỗi khởi động server: {e}")

        self.update_buttons()
        self.stat_signal.emit()

    def stop_server(self):
        self.running = False

        self.close_server_socket()

        self.server_socket = None

        self.status_label.setText("ĐÃ DỪNG")
        self.status_label.setStyleSheet("""
        QLabel {
            background:#831843;
            color:white;
            border:none;
            border-radius:14px;
            font-weight:900;
        }
        """)

        self.log_signal.emit("Server đã dừng.")
        self.update_buttons()
        self.stat_signal.emit()

    def close_server_socket(self):
        if not self.server_socket:
            return
        try:
            self.server_socket.close()
        except Exception:
            pass

    def listen_loop(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                thread.start()

            except Exception:
                break

    def format_addr(self, addr):
        return f"{addr[0]}:{addr[1]}"

    def handle_client(self, client_socket, addr):
        addr_text = self.format_addr(addr)

        try:
            command = self.recv_exact(client_socket, 1).decode(errors="replace")
            if command == "P":
                client_socket.sendall(b"OK")
                return
            if command != "U":
                raise RuntimeError("Lệnh gửi không hợp lệ")

            self.clients[addr] = client_socket
            self.active_transfers += 1
            self.stat_signal.emit()

            dir_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            target_dir = self.recv_exact(client_socket, dir_len).decode(errors="replace") if dir_len > 0 else ""

            name_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            file_name = self.recv_exact(client_socket, name_len).decode(errors="replace")

            file_size = struct.unpack("!Q", self.recv_exact(client_socket, 8))[0]
            duplicate_policy = self.recv_exact(client_socket, 1).decode(errors="replace") or "R"
            expected_hash = self.recv_exact(client_socket, 32)

            safe_name = os.path.basename(file_name)
            safe_dir = self.sanitize_subfolder(target_dir)
            save_dir = os.path.join(self.upload_dir, safe_dir) if safe_dir else self.upload_dir
            os.makedirs(save_dir, exist_ok=True)

            save_path = os.path.join(save_dir, safe_name)

            offset = os.path.getsize(save_path) if os.path.exists(save_path) else 0
            if duplicate_policy == "O":
                offset = 0
            elif os.path.exists(save_path) and duplicate_policy == "N":
                save_path = self.unique_file_path(save_dir, safe_name)
                safe_name = os.path.basename(save_path)
                offset = 0
            elif os.path.exists(save_path) and duplicate_policy == "S":
                offset = file_size
            elif os.path.exists(save_path) and offset >= file_size:
                if self.calculate_file_hash(save_path) != expected_hash:
                    offset = 0

            client_socket.sendall(struct.pack("!Q", offset))

            row_key = f"{addr_text}-{safe_name}"
            self.transfer_signal.emit(row_key, safe_name, addr_text, "0%", "Đang nhận", save_path)

            if offset >= file_size:
                if os.path.exists(save_path) and self.calculate_file_hash(save_path) == expected_hash:
                    client_socket.sendall(SERVER_VERIFY_SKIPPED)
                    self.transfer_signal.emit(row_key, safe_name, addr_text, "100%", "Đã bỏ qua", save_path)
                    self.log_signal.emit(f"Đã xác minh file có sẵn: {safe_name}")
                else:
                    client_socket.sendall(SERVER_VERIFY_FAILED)
                    self.failed_count += 1
                    self.transfer_signal.emit(row_key, safe_name, addr_text, "100%", "Sai checksum", save_path)
                    self.log_signal.emit(f"Checksum không khớp với file có sẵn: {safe_name}")
                return

            received = offset
            last_time = time.time()
            last_received = received
            mode = "ab" if offset > 0 and duplicate_policy not in ("O", "N") else "wb"

            with open(save_path, mode) as f:
                while received < file_size:
                    data = client_socket.recv(CHUNK_SIZE)
                    if not data:
                        break

                    f.write(data)
                    received += len(data)
                    self.total_bytes += len(data)

                    now = time.time()
                    if now - last_time >= TRANSFER_UPDATE_INTERVAL or received >= file_size:
                        percent = int(received * 100 / file_size) if file_size else 100
                        speed = (received - last_received) / max(now - last_time, 0.001)

                        self.transfer_signal.emit(
                            row_key,
                            safe_name,
                            addr_text,
                            f"{percent}%",
                            f"{self.format_bytes(speed)}/s",
                            save_path,
                        )

                        last_time = now
                        last_received = received
                        self.stat_signal.emit()

            actual_hash = self.calculate_file_hash(save_path)
            if actual_hash != expected_hash:
                client_socket.sendall(SERVER_VERIFY_FAILED)
                self.failed_count += 1
                self.transfer_signal.emit(row_key, safe_name, addr_text, "100%", "Sai checksum", save_path)
                self.log_signal.emit(f"Checksum không khớp: {safe_name}")
                return

            client_socket.sendall(SERVER_VERIFY_OK)
            self.total_files += 1
            self.transfer_signal.emit(row_key, safe_name, addr_text, "100%", "Đã xác minh", save_path)
            self.log_signal.emit(f"Nhận xong và xác minh file: {safe_name}")

        except Exception as e:
            self.failed_count += 1
            self.log_signal.emit(f"Lỗi nhận file từ {addr_text}: {e}")

        finally:
            try:
                client_socket.close()
            except Exception:
                pass

            if addr in self.clients:
                del self.clients[addr]

            self.active_transfers = max(0, self.active_transfers - 1)
            self.stat_signal.emit()

    def update_transfer_row(self, key, file_name, addr, progress, status, file_path):
        if key not in self.transfer_rows:
            row = self.transfer_table.rowCount()
            self.transfer_table.insertRow(row)

            self.transfer_rows[key] = row
            self.transfer_paths[key] = file_path

            self.transfer_table.setItem(row, 0, QTableWidgetItem(file_name))
            self.transfer_table.setItem(row, 1, QTableWidgetItem(addr))
            self.transfer_table.setItem(row, 2, QTableWidgetItem(progress))
            self.transfer_table.setItem(row, 3, QTableWidgetItem("--"))
            self.transfer_table.setItem(row, 4, QTableWidgetItem(status))
            open_btn = QPushButton("Mở")
            open_btn.setEnabled(False)
            open_btn.setStyleSheet(self.control_button_style())
            open_btn.clicked.connect(lambda _checked=False, transfer_key=key: self.open_transfer_file(transfer_key))
            self.transfer_table.setCellWidget(row, 5, open_btn)
        else:
            row = self.transfer_rows[key]
            self.transfer_paths[key] = file_path
            self.transfer_table.setItem(row, 2, QTableWidgetItem(progress))

            if status.endswith("/s"):
                self.transfer_table.setItem(row, 3, QTableWidgetItem(status))
                self.transfer_table.setItem(row, 4, QTableWidgetItem("Đang nhận"))
            else:
                self.transfer_table.setItem(row, 4, QTableWidgetItem(status))

        row = self.transfer_rows[key]
        open_btn = self.transfer_table.cellWidget(row, 5)
        if open_btn:
            can_open = os.path.exists(file_path) and status in ("Đã xác minh", "Đã bỏ qua")
            open_btn.setEnabled(can_open)

    def open_transfer_file(self, key):
        file_path = self.transfer_paths.get(key)
        if not file_path or not os.path.exists(file_path):
            self.log_signal.emit("Không tìm thấy tệp để mở.")
            return
        try:
            os.startfile(file_path)
            self.log_signal.emit(f"Đã mở tệp: {file_path}")
        except Exception as e:
            self.log_signal.emit(f"Không thể mở tệp: {e}")

    def update_stats(self):
        self.lbl_clients.value_label.setText(str(len(self.clients)))
        self.lbl_transfers.value_label.setText(str(self.active_transfers))
        self.lbl_files.value_label.setText(str(self.total_files))
        self.lbl_data.value_label.setText(self.format_bytes(self.total_bytes))
        self.lbl_errors.value_label.setText(str(self.failed_count))

        if self.running and self.started_at:
            sec = int(time.time() - self.started_at)
            self.lbl_time.value_label.setText(self.format_duration(sec))
        else:
            self.lbl_time.value_label.setText("--")

    def update_buttons(self):
        self.start_btn.setEnabled(not self.running)
        self.stop_btn.setEnabled(self.running)
        self.host_input.setEnabled(not self.running)
        self.port_input.setEnabled(not self.running)
        self.folder_input.setEnabled(not self.running)

    def add_log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{now}] {message}")

    def recv_exact(self, sock, size):
        chunks = []
        received = 0

        while received < size:
            chunk = sock.recv(size - received)
            if not chunk:
                raise ConnectionError("Kết nối bị đóng.")
            chunks.append(chunk)
            received += len(chunk)

        return b"".join(chunks)

    def sanitize_subfolder(self, folder_name):
        folder_name = (folder_name or "").strip().replace("\\", "/")
        parts = []
        for part in folder_name.split("/"):
            part = part.strip().strip(".")
            if part:
                parts.append(part)
        return os.path.join(*parts) if parts else ""

    def unique_file_path(self, folder, file_name):
        stem, ext = os.path.splitext(file_name)
        candidate = os.path.join(folder, file_name)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{stem} ({counter}){ext}")
            counter += 1
        return candidate

    def calculate_file_hash(self, file_path):
        digest = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(HASH_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.digest()

    def get_lan_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

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
