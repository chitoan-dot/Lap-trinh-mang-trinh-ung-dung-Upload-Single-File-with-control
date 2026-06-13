import os
import threading
import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFrame, QHBoxLayout, QProgressBar, QFileDialog, QMessageBox, QComboBox
)

from client.socket_client import SocketClient
from client.upload_history import add_upload_record
from client.upload_manager import UploadManager
from common.constants import SERVER_ERROR_OFFSET
from layout.theme import *
from layout.style import *

# THÊM: lưu dữ liệu upload sang SQL Server
try:
    from Database.db_manager import save_uploaded_file, save_upload_log
except Exception:
    save_uploaded_file = None
    save_upload_log = None


SPEED_LIMITS = {
    "Không giới hạn": 0,
    "2 MB/s": 2 * 1024 * 1024,
    "5 MB/s": 5 * 1024 * 1024,
    "10 MB/s": 10 * 1024 * 1024,
}

DUPLICATE_POLICIES = {
    "Bỏ qua nếu file đã có": "S",
    "Ghi đè file cũ": "O",
    "Đổi tên tự động": "N",
    "Tiếp tục file đang dở": "R",
}


class DropArea(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        local_files = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if local_files:
            self.file_dropped.emit(local_files[0])
            event.acceptProposedAction()
        else:
            event.ignore()


class UploadUI(QWidget):
    progress_signal = pyqtSignal(int, str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    server_status_signal = pyqtSignal(bool, str)

    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.user_email = str(self.current_user.get("email", "")).strip().lower()
        self.user_name = str(self.current_user.get("full_name", "")).strip()
        self.selected_file = None
        self.upload_state = "stopped"
        self.upload_thread = None
        self.socket_client = None
        self.server_host = "127.0.0.1"
        self.server_port = 8888
        self.last_upload_file_path = ""
        self.last_upload_file_size = 0

        self.setAcceptDrops(True)
        self.setStyleSheet(PAGE_STYLE)
        self.build_ui()

        self.progress_signal.connect(self.on_progress)
        self.status_signal.connect(self.set_status)
        self.finished_signal.connect(self.on_finished)
        self.server_status_signal.connect(self.set_server_status)
        self.check_server_connection_async()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)

        title = QLabel("Upload file")
        title.setStyleSheet(f"color:{TEXT}; font-size:32px; font-weight:900;")

        subtitle = QLabel("Gửi một file lên Server với các nút Start, Pause, Resume và Stop")
        subtitle.setStyleSheet(f"color:{TEXT2}; font-size:17px;")

        server_row = QHBoxLayout()
        server_row.setSpacing(12)

        self.server_status_label = QLabel(f"Server: Đang kiểm tra {self.server_host}:{self.server_port}")
        self.server_status_label.setFixedHeight(42)
        self.server_status_label.setStyleSheet(self.server_status_style(False))

        self.check_server_btn = QPushButton("Kiểm tra")
        self.check_server_btn.setFixedSize(118, 42)
        self.check_server_btn.setStyleSheet(self.secondary_button_style())
        self.check_server_btn.clicked.connect(self.check_server_connection_async)

        server_row.addWidget(self.server_status_label)
        server_row.addWidget(self.check_server_btn)

        upload_area = DropArea()
        upload_area.file_dropped.connect(self.set_selected_file)
        upload_area.setFixedHeight(460)
        upload_area.setStyleSheet(f"""
            QFrame {{
                background:transparent;
                border:2px dashed {BORDER};
                border-radius:18px;
            }}
            QFrame:hover {{
                background:#111827;
                border:2px dashed {PRIMARY};
            }}
        """)

        area = QVBoxLayout(upload_area)
        area.setContentsMargins(0, 0, 0, 0)
        area.setSpacing(0)

        center = QFrame()
        center.setFixedWidth(620)
        center.setStyleSheet("background:transparent; border:none;")

        box = QVBoxLayout(center)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(10)
        box.setAlignment(Qt.AlignHCenter)

        icon = QLabel("⇧")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(80, 80)
        icon.setStyleSheet("""
            background:#321750;
            color:#c084fc;
            border-radius:40px;
            font-size:48px;
            border:none;
        """)

        drop_title = QLabel("Thả file vào đây hoặc bấm để chọn")
        drop_title.setAlignment(Qt.AlignCenter)
        drop_title.setStyleSheet(f"""
            color:{TEXT};
            font-size:24px;
            font-weight:900;
            border:none;
            background:transparent;
        """)

        self.file_label = QLabel("Chưa chọn file nào")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet(f"""
            color:{TEXT2};
            font-size:18px;
            border:none;
            background:transparent;
        """)

        self.browse_btn = QPushButton("Chọn file")
        self.browse_btn.setFixedSize(220, 58)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background:{GRADIENT};
                color:white;
                border:none;
                border-radius:14px;
                font-size:18px;
                font-weight:bold;
            }}
            QPushButton:hover {{
                background:#ec4899;
            }}
            QPushButton:pressed {{
                background:#c026d3;
            }}
        """)
        self.browse_btn.clicked.connect(self.pick_file)

        self.info_label = QLabel("File: Chưa chọn file  |  Dung lượng: 0 MB  |  Trạng thái: Sẵn sàng")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            color:#94a3b8;
            font-size:15px;
            border:none;
            background:transparent;
        """)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedWidth(500)
        self.progress.setFixedHeight(18)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background:#1e293b;
                color:white;
                border:none;
                border-radius:8px;
                text-align:center;
            }}
            QProgressBar::chunk {{
                background:{PINK};
                border-radius:8px;
            }}
        """)

        controls = QHBoxLayout()
        controls.setAlignment(Qt.AlignCenter)
        controls.setSpacing(22)

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")

        for btn in [self.start_btn, self.pause_btn, self.resume_btn, self.stop_btn]:
            btn.setFixedSize(110, 44)
            btn.setStyleSheet(BUTTON_STYLE)
            controls.addWidget(btn)

        self.start_btn.clicked.connect(self.start_upload)
        self.pause_btn.clicked.connect(self.pause_upload)
        self.resume_btn.clicked.connect(self.resume_upload)
        self.stop_btn.clicked.connect(self.stop_upload)

        speed_row = QHBoxLayout()
        speed_row.setAlignment(Qt.AlignCenter)
        speed_row.setSpacing(10)

        speed_label = QLabel("Tốc độ demo:")
        speed_label.setStyleSheet("color:#94a3b8; font-size:14px; border:none; background:transparent;")

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(list(SPEED_LIMITS.keys()))
        self.speed_combo.setCurrentText("5 MB/s")
        self.speed_combo.setFixedSize(180, 36)
        self.speed_combo.setStyleSheet(f"""
            QComboBox {{
                background:{CARD2};
                color:{TEXT};
                border:1px solid #334155;
                border-radius:10px;
                padding-left:10px;
            }}
            QComboBox:hover {{
                border:1px solid {PRIMARY};
                background:#171832;
            }}
            QComboBox::drop-down {{
                border:none;
                width:26px;
            }}
            QComboBox QAbstractItemView {{
                background:{CARD2};
                color:{TEXT};
                selection-background-color:{PRIMARY};
                border:1px solid {BORDER};
            }}
        """)

        policy_label = QLabel("File trùng:")
        policy_label.setStyleSheet("color:#94a3b8; font-size:14px; border:none; background:transparent;")

        self.policy_combo = QComboBox()
        self.policy_combo.addItems(list(DUPLICATE_POLICIES.keys()))
        self.policy_combo.setCurrentText("Bỏ qua nếu file đã có")
        self.policy_combo.setFixedSize(210, 36)
        self.policy_combo.setStyleSheet(self.speed_combo.styleSheet())

        speed_row.addWidget(speed_label)
        speed_row.addWidget(self.speed_combo)
        speed_row.addWidget(policy_label)
        speed_row.addWidget(self.policy_combo)

        box.addWidget(icon, 0, Qt.AlignHCenter)
        box.addSpacing(18)
        box.addWidget(drop_title, 0, Qt.AlignHCenter)
        box.addSpacing(8)
        box.addWidget(self.file_label, 0, Qt.AlignHCenter)
        box.addSpacing(18)
        box.addWidget(self.browse_btn, 0, Qt.AlignHCenter)
        box.addSpacing(12)
        box.addWidget(self.info_label, 0, Qt.AlignHCenter)
        box.addWidget(self.progress, 0, Qt.AlignHCenter)
        box.addSpacing(8)
        box.addLayout(controls)
        box.addLayout(speed_row)

        area.addStretch()
        area.addWidget(center, 0, Qt.AlignCenter)
        area.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(server_row)
        layout.addWidget(upload_area)
        layout.addStretch()
        self.update_buttons()

    def secondary_button_style(self):
        return f"""
        QPushButton {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:12px;
            font-size:14px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        QPushButton:disabled {{
            color:#64748b;
            border:1px solid #26324a;
        }}
        """

    def server_status_style(self, connected):
        if connected:
            return f"""
            QLabel {{
                background:#052e24;
                color:{GREEN};
                border:1px solid #0f766e;
                border-radius:12px;
                padding-left:14px;
                font-size:14px;
                font-weight:bold;
            }}
            """
        return f"""
        QLabel {{
            background:#2a1425;
            color:#fda4af;
            border:1px solid #7f1d1d;
            border-radius:12px;
            padding-left:14px;
            font-size:14px;
            font-weight:bold;
        }}
        """

    def set_server_status(self, connected, message):
        self.server_status_label.setText(message)
        self.server_status_label.setStyleSheet(self.server_status_style(connected))
        if hasattr(self, "check_server_btn"):
            self.check_server_btn.setEnabled(self.upload_state == "stopped")

    def probe_server_connection(self):
        client = SocketClient(self.server_host, self.server_port, timeout=1.5)
        try:
            sock = client.connect()
            sock.settimeout(1.5)
            sock.sendall(b"P")
            return sock.recv(2) == b"OK"
        except Exception:
            return False
        finally:
            client.close()

    def check_server_connection_async(self):
        if hasattr(self, "check_server_btn"):
            self.check_server_btn.setEnabled(False)
        self.server_status_signal.emit(
            False,
            f"Server: Đang kiểm tra {self.server_host}:{self.server_port}",
        )
        threading.Thread(target=self.check_server_connection_worker, daemon=True).start()

    def check_server_connection_worker(self):
        connected = self.probe_server_connection()
        if connected:
            message = f"Server: Đã kết nối {self.server_host}:{self.server_port}"
        else:
            message = f"Server: Chưa kết nối {self.server_host}:{self.server_port}"
        self.server_status_signal.emit(connected, message)

    def pick_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file")
        if not file_path:
            return
        self.set_selected_file(file_path)

    def set_selected_file(self, file_path):
        if self.upload_state != "stopped":
            QMessageBox.warning(self, "UPLOWER", "Không thể đổi file khi đang upload.")
            return
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "UPLOWER", "Vui lòng chọn một file hợp lệ.")
            return

        self.selected_file = file_path
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        self.file_label.setText(filename)
        self.info_label.setText(f"File: {filename}  |  Dung lượng: {self.format_bytes(size)}  |  Trạng thái: Sẵn sàng")
        self.progress.setValue(0)
        self.update_buttons()

    def dragEnterEvent(self, event):
        if self.upload_state != "stopped":
            event.ignore()
            return

        mime = event.mimeData()
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        if self.upload_state != "stopped":
            event.ignore()
            return

        local_files = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

        if not local_files:
            event.ignore()
            return

        file_path = local_files[0]
        if os.path.isdir(file_path):
            QMessageBox.warning(self, "UPLOWER", "Chức năng này chỉ hỗ trợ kéo thả một file, không hỗ trợ thư mục.")
            event.ignore()
            return

        self.set_selected_file(file_path)
        event.acceptProposedAction()

    def start_upload(self):
        if not self.selected_file:
            QMessageBox.warning(self, "UPLOWER", "Bạn chưa chọn file để upload.")
            return
        if not self.probe_server_connection():
            self.set_server_status(False, f"Server: Chưa kết nối {self.server_host}:{self.server_port}")
            QMessageBox.warning(self, "UPLOWER", "Server chưa sẵn sàng. Vui lòng bật Server bên Admin rồi thử lại.")
            return
        self.set_server_status(True, f"Server: Đã kết nối {self.server_host}:{self.server_port}")
        if self.upload_state == "uploading":
            return
        self.upload_state = "uploading"
        self.update_buttons()
        self.upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        self.upload_thread.start()

    def pause_upload(self):
        if self.upload_state == "uploading":
            self.upload_state = "paused"

            # THÊM: lưu log pause vào SQL Server
            if save_upload_log:
                try:
                    save_upload_log(
                        user_email=self.user_email,
                        action="pause_upload",
                        description=f"Tạm dừng upload {os.path.basename(self.selected_file)}"
                    )
                except Exception as e:
                    print("SQL Server log pause error:", e)

            self.set_status("Đã tạm dừng")
            self.update_buttons()

    def resume_upload(self):
        if self.upload_state == "paused":
            self.upload_state = "uploading"

            # THÊM: lưu log resume vào SQL Server
            if save_upload_log:
                try:
                    save_upload_log(
                        user_email=self.user_email,
                        action="resume_upload",
                        description=f"Tiếp tục upload {os.path.basename(self.selected_file)}"
                    )
                except Exception as e:
                    print("SQL Server log resume error:", e)

            self.set_status("Đang upload")
            self.update_buttons()

    def stop_upload(self):
        if self.upload_state in ("uploading", "paused"):

            # THÊM: lưu log stop vào SQL Server
            if save_upload_log:
                try:
                    save_upload_log(
                        user_email=self.user_email,
                        action="stop_upload",
                        description=f"Dừng upload {os.path.basename(self.selected_file)}"
                    )
                except Exception as e:
                    print("SQL Server log stop error:", e)

            self.upload_state = "stopped"
            if self.socket_client:
                self.socket_client.close()
            self.set_status("Đã dừng")
            self.update_buttons()

    def upload_worker(self):
        file_path = self.selected_file
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        start_time = time.time()
        server_text = f"{self.server_host}:{self.server_port}"
        self.last_upload_file_path = file_path
        self.last_upload_file_size = file_size

        try:
            self.socket_client = SocketClient(self.server_host, self.server_port)
            sock = self.socket_client.connect()
            manager = UploadManager(sock)
            duplicate_policy = DUPLICATE_POLICIES.get(self.policy_combo.currentText(), "S")
            offset = manager.prepare_upload(file_path, target_dir="", duplicate_policy=duplicate_policy)

            if offset == SERVER_ERROR_OFFSET:
                raise RuntimeError("Server không đủ dung lượng để nhận file.")

            if offset >= file_size:
                manager.receive_verify_status()
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Skipped",
                    message="File already existed on server",
                    user_email=self.user_email,
                    user_name=self.user_name,
                )

                # THÊM: lưu log skipped vào SQL Server
                if save_upload_log:
                    try:
                        save_upload_log(
                            user_email=self.user_email,
                            action="upload_skipped",
                            description=f"File đã tồn tại trên server: {file_name}"
                        )
                    except Exception as e:
                        print("SQL Server log skipped error:", e)

                self.progress_signal.emit(100, f"File: {file_name}  |  Dung lượng: {self.format_bytes(file_size)}  |  Trạng thái: Skipped")
                self.finished_signal.emit(True, "File đã có trên server và đã được xác minh.")
                return

            last_time = time.time()
            last_sent = offset

            def on_chunk(sent, _chunk_size):
                nonlocal last_time, last_sent
                now = time.time()
                if now - last_time >= 0.25 or sent >= file_size:
                    percent = int(sent * 100 / file_size) if file_size else 100
                    delta = sent - last_sent
                    speed = delta / max(now - last_time, 0.001)
                    text = (
                        f"File: {file_name}  |  Dung lượng: {self.format_bytes(file_size)}  |  "
                        f"Trạng thái: Đang upload {percent}%  |  Tốc độ: {self.format_bytes(speed)}/s"
                    )
                    self.progress_signal.emit(percent, text)
                    last_time = now
                    last_sent = sent

            manager.stream_file(
                file_path,
                offset=offset,
                on_chunk=on_chunk,
                should_stop=lambda: self.upload_state == "stopped",
                should_pause=lambda: self.upload_state == "paused",
                speed_limit=SPEED_LIMITS.get(self.speed_combo.currentText(), 0),
            )

            if self.upload_state == "stopped":
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Stopped",
                    message="Upload stopped by user",
                    user_email=self.user_email,
                    user_name=self.user_name,
                )
                self.finished_signal.emit(False, "Đã dừng upload.")
            else:
                manager.receive_verify_status()
                elapsed = max(time.time() - start_time, 1)
                avg_speed = file_size / elapsed
                speed_text = f"{self.format_bytes(avg_speed)}/s"
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Verified",
                    speed=speed_text,
                    user_email=self.user_email,
                    user_name=self.user_name,
                )

                # THÊM: upload thành công thì lưu file + log vào SQL Server
                if save_uploaded_file or save_upload_log:
                    try:
                        file_hash = ""
                        try:
                            file_hash = manager.calculate_file_hash(file_path)
                        except Exception:
                            file_hash = ""

                        if save_uploaded_file:
                            save_uploaded_file(
                                user_email=self.user_email,
                                file_name=file_name,
                                file_size=file_size,
                                file_hash=file_hash,
                                file_path=file_path,
                                status="uploaded"
                            )

                        if save_upload_log:
                            save_upload_log(
                                user_email=self.user_email,
                                action="upload_completed",
                                description=f"Upload thành công {file_name}"
                            )

                    except Exception as e:
                        print("SQL Server save upload error:", e)

                self.progress_signal.emit(
                    100,
                    f"File: {file_name}  |  Dung lượng: {self.format_bytes(file_size)}  |  Trạng thái: Verified  |  Trung bình: {speed_text}"
                )
                self.finished_signal.emit(True, "Upload file thành công và checksum đã khớp.")
        except Exception as e:
            if self.upload_state == "stopped":
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Stopped",
                    message="Upload stopped by user",
                    user_email=self.user_email,
                    user_name=self.user_name,
                )
            else:
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Failed",
                    message=str(e),
                    user_email=self.user_email,
                    user_name=self.user_name,
                )

                # THÊM: upload lỗi thì lưu log vào SQL Server
                if save_upload_log:
                    try:
                        save_upload_log(
                            user_email=self.user_email,
                            action="upload_failed",
                            description=f"Upload thất bại {file_name}: {e}"
                        )
                    except Exception as log_error:
                        print("SQL Server log failed error:", log_error)

            self.finished_signal.emit(False, f"Upload thất bại: {e}")
        finally:
            if self.socket_client:
                self.socket_client.close()
                self.socket_client = None
            if self.upload_state != "paused":
                self.upload_state = "stopped"

    def on_progress(self, percent, text):
        self.progress.setValue(percent)
        self.info_label.setText(text)

    def set_status(self, status):
        if self.selected_file:
            self.info_label.setText(f"File: {os.path.basename(self.selected_file)}  |  Trạng thái: {status}")

    def on_finished(self, success, message):
        self.upload_state = "stopped"
        self.update_buttons()
        if success:
            QMessageBox.information(self, "UPLOWER", message)
        else:
            QMessageBox.warning(self, "UPLOWER", message)

    def update_buttons(self):
        has_file = self.selected_file is not None
        self.start_btn.setEnabled(has_file and self.upload_state == "stopped")
        self.pause_btn.setEnabled(self.upload_state == "uploading")
        self.resume_btn.setEnabled(self.upload_state == "paused")
        self.stop_btn.setEnabled(self.upload_state in ("uploading", "paused"))
        self.browse_btn.setEnabled(self.upload_state == "stopped")
        self.speed_combo.setEnabled(self.upload_state == "stopped")
        self.policy_combo.setEnabled(self.upload_state == "stopped")
        if hasattr(self, "check_server_btn"):
            self.check_server_btn.setEnabled(self.upload_state == "stopped")

    def format_bytes(self, value):
        value = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024