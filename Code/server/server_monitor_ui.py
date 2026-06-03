import os
import socket
import threading
import struct
import time
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *

from layout.theme import *


class ServerMonitorUI(QWidget):
    log_signal = pyqtSignal(str)
    stat_signal = pyqtSignal()
    transfer_signal = pyqtSignal(str, str, str, str, str)

    def __init__(self):
        super().__init__()

        self.host = "0.0.0.0"
        self.port = 8888
        self.upload_dir = os.path.abspath("Uploads")

        self.server_socket = None
        self.running = False
        self.listen_thread = None

        self.clients = {}
        self.transfer_rows = {}

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

        QFrame#StatCard {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
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

        title_box = QVBoxLayout()

        title = QLabel("Máy Chủ Nhận Tệp")
        title.setStyleSheet("""
        QLabel {
            font-size:36px;
            font-weight:900;
            color:white;
            border:none;
            background:transparent;
        }
        """)

        subtitle = QLabel("Bật server, theo dõi thiết bị gửi và phiên nhận file")
        subtitle.setStyleSheet(f"""
        QLabel {{
            font-size:18px;
            color:{TEXT2};
            border:none;
            background:transparent;
        }}
        """)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.host_input = QLineEdit(self.host)
        self.host_input.setFixedSize(140, 52)

        self.port_input = QLineEdit(str(self.port))
        self.port_input.setFixedSize(110, 52)

        self.status_label = QLabel("ĐÃ DỪNG")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedSize(120, 52)
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
        self.start_btn.setFixedSize(120, 52)
        self.start_btn.setStyleSheet(self.primary_button_style())
        self.start_btn.clicked.connect(self.start_server)

        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setFixedSize(120, 52)
        self.stop_btn.setStyleSheet(self.danger_button_style())
        self.stop_btn.clicked.connect(self.stop_server)

        top.addLayout(title_box)
        top.addStretch()
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
        self.transfer_table.setColumnCount(5)
        self.transfer_table.setHorizontalHeaderLabels(
            ["Tệp", "Thiết bị gửi", "Tiến trình", "Tốc độ", "Trạng thái"]
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
        self.log_signal.emit("Server monitor sẵn sàng.")

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
        }}
        """

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file")
        if folder:
            self.upload_dir = folder
            self.folder_input.setText(folder)
            self.log_signal.emit(f"Đã chọn thư mục lưu: {folder}")

    def start_server(self):
        if self.running:
            return

        try:
            self.host = self.host_input.text().strip() or "0.0.0.0"
            self.port = int(self.port_input.text().strip() or "8888")
            self.upload_dir = self.folder_input.text().strip() or os.path.abspath("Uploads")
            os.makedirs(self.upload_dir, exist_ok=True)

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)

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
            self.log_signal.emit(f"Server đang chạy tại {self.host}:{self.port}")

        except Exception as e:
            self.running = False
            self.log_signal.emit(f"Lỗi khởi động server: {e}")

        self.update_buttons()
        self.stat_signal.emit()

    def stop_server(self):
        self.running = False

        try:
            if self.server_socket:
                self.server_socket.close()
        except Exception:
            pass

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

    def listen_loop(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.clients[addr] = client_socket
                self.active_transfers += 1
                self.stat_signal.emit()

                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                thread.start()

            except Exception:
                break

    def handle_client(self, client_socket, addr):
        addr_text = f"{addr[0]}:{addr[1]}"

        try:
            command = self.recv_exact(client_socket, 1).decode(errors="replace")
            if command != "U":
                raise RuntimeError("Lệnh gửi không hợp lệ")

            dir_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            target_dir = self.recv_exact(client_socket, dir_len).decode(errors="replace") if dir_len > 0 else ""

            name_len = struct.unpack("!I", self.recv_exact(client_socket, 4))[0]
            file_name = self.recv_exact(client_socket, name_len).decode(errors="replace")

            file_size = struct.unpack("!Q", self.recv_exact(client_socket, 8))[0]
            duplicate_policy = self.recv_exact(client_socket, 1).decode(errors="replace") or "R"

            safe_name = os.path.basename(file_name)
            save_dir = os.path.join(self.upload_dir, target_dir) if target_dir else self.upload_dir
            os.makedirs(save_dir, exist_ok=True)

            save_path = os.path.join(save_dir, safe_name)

            offset = os.path.getsize(save_path) if os.path.exists(save_path) else 0
            if duplicate_policy == "O":
                offset = 0

            client_socket.sendall(struct.pack("!Q", offset))

            row_key = f"{addr_text}-{safe_name}"
            self.transfer_signal.emit(row_key, safe_name, addr_text, "0%", "Đang nhận")

            received = offset
            last_time = time.time()
            last_received = received
            mode = "ab" if offset > 0 else "wb"

            with open(save_path, mode) as f:
                while received < file_size:
                    data = client_socket.recv(65536)
                    if not data:
                        break

                    f.write(data)
                    received += len(data)
                    self.total_bytes += len(data)

                    now = time.time()
                    if now - last_time >= 0.25 or received >= file_size:
                        percent = int(received * 100 / file_size) if file_size else 100
                        speed = (received - last_received) / max(now - last_time, 0.001)

                        self.transfer_signal.emit(
                            row_key,
                            safe_name,
                            addr_text,
                            f"{percent}%",
                            f"{self.format_bytes(speed)}/s"
                        )

                        last_time = now
                        last_received = received
                        self.stat_signal.emit()

            self.total_files += 1
            self.transfer_signal.emit(row_key, safe_name, addr_text, "100%", "Hoàn tất")
            self.log_signal.emit(f"Nhận xong file: {safe_name}")

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

    def update_transfer_row(self, key, file_name, addr, progress, status):
        if key not in self.transfer_rows:
            row = self.transfer_table.rowCount()
            self.transfer_table.insertRow(row)

            self.transfer_rows[key] = row

            self.transfer_table.setItem(row, 0, QTableWidgetItem(file_name))
            self.transfer_table.setItem(row, 1, QTableWidgetItem(addr))
            self.transfer_table.setItem(row, 2, QTableWidgetItem(progress))
            self.transfer_table.setItem(row, 3, QTableWidgetItem("--"))
            self.transfer_table.setItem(row, 4, QTableWidgetItem(status))
        else:
            row = self.transfer_rows[key]
            self.transfer_table.setItem(row, 2, QTableWidgetItem(progress))

            if status.endswith("/s"):
                self.transfer_table.setItem(row, 3, QTableWidgetItem(status))
                self.transfer_table.setItem(row, 4, QTableWidgetItem("Đang nhận"))
            else:
                self.transfer_table.setItem(row, 4, QTableWidgetItem(status))

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