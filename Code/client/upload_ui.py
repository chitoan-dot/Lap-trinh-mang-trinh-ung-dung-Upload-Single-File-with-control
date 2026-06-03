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


class UploadUI(QWidget):
    progress_signal = pyqtSignal(int, str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

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

        self.setStyleSheet(PAGE_STYLE)
        self.build_ui()

        self.progress_signal.connect(self.on_progress)
        self.status_signal.connect(self.set_status)
        self.finished_signal.connect(self.on_finished)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)

        title = QLabel("Upload file")
        title.setStyleSheet(f"color:{TEXT}; font-size:32px; font-weight:900;")

        subtitle = QLabel("Gửi một file lên Server với các nút Start, Pause, Resume và Stop")
        subtitle.setStyleSheet(f"color:{TEXT2}; font-size:17px;")

        upload_area = QFrame()
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
        layout.addWidget(upload_area)
        layout.addStretch()
        self.update_buttons()

    def pick_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file")
        if not file_path:
            return
        self.selected_file = file_path
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        self.file_label.setText(filename)
        self.info_label.setText(f"File: {filename}  |  Dung lượng: {self.format_bytes(size)}  |  Trạng thái: Sẵn sàng")
        self.progress.setValue(0)
        self.update_buttons()

    def start_upload(self):
        if not self.selected_file:
            QMessageBox.warning(self, "UPLOWER", "Bạn chưa chọn file để upload.")
            return
        if self.upload_state == "uploading":
            return
        self.upload_state = "uploading"
        self.update_buttons()
        self.upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        self.upload_thread.start()

    def pause_upload(self):
        if self.upload_state == "uploading":
            self.upload_state = "paused"
            self.set_status("Đã tạm dừng")
            self.update_buttons()

    def resume_upload(self):
        if self.upload_state == "paused":
            self.upload_state = "uploading"
            self.set_status("Đang upload")
            self.update_buttons()

    def stop_upload(self):
        if self.upload_state in ("uploading", "paused"):
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

    def format_bytes(self, value):
        value = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024
