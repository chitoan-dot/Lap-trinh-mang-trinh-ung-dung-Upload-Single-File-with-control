import os
import queue
import threading
import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFrame, QHBoxLayout, QProgressBar, QFileDialog, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from client.socket_client import SocketClient
from client.upload_history import add_upload_record
from client.upload_manager import UploadManager
from common.config import client_server_address
from common.constants import CHUNK_SIZE, SERVER_ERROR_OFFSET
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

CHUNK_SIZE_OPTIONS = {
    "1 MB": 1 * 1024 * 1024,
    "5 MB": 5 * 1024 * 1024,
    "10 MB": 10 * 1024 * 1024,
}

THREAD_OPTIONS = {
    "1": 1,
    "2": 2,
    "4": 4,
}

DEFAULT_DUPLICATE_POLICY = "S"
MAX_VISIBLE_CHUNK_ROWS = 500
SERVER_DISCONNECT_MESSAGE = (
    "Mất kết nối tới Server trong khi upload. "
    "Server có thể đã bị tắt hoặc ngắt kết nối. "
    "Vui lòng bật lại Server rồi thử lại."
)
EMPTY_FILE_MESSAGE = "File rỗng 0 byte không hợp lệ. Vui lòng chọn file có dữ liệu để upload."


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
    chunk_status_signal = pyqtSignal(int, str, int)
    chunk_summary_signal = pyqtSignal(int, int, str)

    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.user_email = str(self.current_user.get("email", "")).strip().lower()
        self.user_name = str(self.current_user.get("full_name", "")).strip()
        self.selected_file = None
        self.upload_state = "stopped"
        self.upload_thread = None
        self.socket_client = None
        self.server_host, self.server_port = client_server_address()
        self.last_upload_file_path = ""
        self.last_upload_file_size = 0
        self.current_chunk_ranges = []

        self.setAcceptDrops(True)
        self.setStyleSheet(PAGE_STYLE)
        self.build_ui()

        self.progress_signal.connect(self.on_progress)
        self.status_signal.connect(self.set_status)
        self.finished_signal.connect(self.on_finished)
        self.server_status_signal.connect(self.set_server_status)
        self.chunk_status_signal.connect(self.update_chunk_status)
        self.chunk_summary_signal.connect(self.update_chunk_summary)
        self.check_server_connection_async()

    def is_server_disconnect_error(self, error):
        text = str(error).lower()
        winerror = getattr(error, "winerror", None)
        if winerror in (10053, 10054, 10060, 10061):
            return True
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        markers = (
            "winerror 10053",
            "winerror 10054",
            "winerror 10060",
            "winerror 10061",
            "connectionrefusederror",
            "connectionreseterror",
            "no connection could be made",
            "actively refused",
            "forcibly closed",
            "kết nối bị đóng",
            "connection timed out",
            "timed out",
        )
        return any(marker in text for marker in markers)

    def upload_failure_message(self, error, multipart=False):
        if self.is_server_disconnect_error(error):
            return SERVER_DISCONNECT_MESSAGE
        prefix = "Upload multi-chunk thất bại" if multipart else "Upload thất bại"
        return f"{prefix}: {error}"

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 28, 35, 24)
        layout.setSpacing(12)

        title = QLabel("Upload file")
        title.setStyleSheet(f"color:{TEXT}; font-size:30px; font-weight:900;")

        subtitle = QLabel("Gửi một file lên Server với các nút Start, Pause, Resume và Stop")
        subtitle.setStyleSheet(f"color:{TEXT2}; font-size:16px;")

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
        upload_area.setFixedHeight(338)
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
        center.setFixedWidth(760)
        center.setStyleSheet("background:transparent; border:none;")

        box = QVBoxLayout(center)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(8)
        box.setAlignment(Qt.AlignHCenter)

        icon = QLabel("⇧")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(58, 58)
        icon.setStyleSheet("""
            background:#321750;
            color:#c084fc;
            border-radius:29px;
            font-size:34px;
            border:none;
        """)

        drop_title = QLabel("Thả file vào đây hoặc bấm để chọn")
        drop_title.setAlignment(Qt.AlignCenter)
        drop_title.setStyleSheet(f"""
            color:{TEXT};
            font-size:22px;
            font-weight:900;
            border:none;
            background:transparent;
        """)

        self.file_label = QLabel("Chưa chọn file nào")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet(f"""
            color:{TEXT2};
            font-size:16px;
            border:none;
            background:transparent;
        """)

        self.browse_btn = QPushButton("Chọn file")
        self.browse_btn.setFixedSize(190, 46)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background:{GRADIENT};
                color:white;
                border:none;
                border-radius:14px;
                font-size:16px;
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

        self.clear_file_btn = QPushButton("Xóa file")
        self.clear_file_btn.setFixedSize(132, 46)
        self.clear_file_btn.setCursor(Qt.PointingHandCursor)
        self.clear_file_btn.setStyleSheet(f"""
            QPushButton {{
                background:#2a1425;
                color:#fecdd3;
                border:1px solid #7f1d1d;
                border-radius:14px;
                font-size:15px;
                font-weight:bold;
            }}
            QPushButton:hover {{
                background:#3b1628;
                color:white;
                border:1px solid #fb7185;
            }}
            QPushButton:pressed {{
                background:#881337;
                color:white;
            }}
            QPushButton:disabled {{
                background:#141827;
                color:#64748b;
                border:1px solid #26324a;
            }}
        """)
        self.clear_file_btn.clicked.connect(self.clear_selected_file)

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
        self.progress.setFixedWidth(520)
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
        controls.setSpacing(12)

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")

        for btn in [self.start_btn, self.pause_btn, self.resume_btn, self.stop_btn]:
            btn.setFixedSize(104, 40)
            btn.setStyleSheet(BUTTON_STYLE)
            controls.addWidget(btn)

        self.start_btn.clicked.connect(self.start_upload)
        self.pause_btn.clicked.connect(self.pause_upload)
        self.resume_btn.clicked.connect(self.resume_upload)
        self.stop_btn.clicked.connect(self.stop_upload)

        chunk_row = QHBoxLayout()
        chunk_row.setAlignment(Qt.AlignCenter)
        chunk_row.setSpacing(12)

        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setStyleSheet("color:#94a3b8; font-size:14px; border:none; background:transparent;")

        speed_label = QLabel("Tốc độ upload:")
        speed_label.setStyleSheet("color:#94a3b8; font-size:14px; border:none; background:transparent;")

        thread_label = QLabel("Threads:")
        thread_label.setStyleSheet("color:#94a3b8; font-size:14px; border:none; background:transparent;")

        self.chunk_size_combo = QComboBox()
        self.chunk_size_combo.addItems(list(CHUNK_SIZE_OPTIONS.keys()))
        self.chunk_size_combo.setCurrentText("5 MB")
        self.chunk_size_combo.setFixedSize(104, 34)
        self.chunk_size_combo.currentTextChanged.connect(self.refresh_chunk_plan)

        self.thread_combo = QComboBox()
        self.thread_combo.addItems(list(THREAD_OPTIONS.keys()))
        self.thread_combo.setCurrentText("4")
        self.thread_combo.setFixedSize(72, 34)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(list(SPEED_LIMITS.keys()))
        self.speed_combo.setCurrentText("5 MB/s")
        self.speed_combo.setFixedSize(155, 34)
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
        self.chunk_size_combo.setStyleSheet(self.speed_combo.styleSheet())
        self.thread_combo.setStyleSheet(self.speed_combo.styleSheet())

        chunk_row.addWidget(chunk_size_label)
        chunk_row.addWidget(self.chunk_size_combo)
        chunk_row.addSpacing(8)
        chunk_row.addWidget(thread_label)
        chunk_row.addWidget(self.thread_combo)
        chunk_row.addSpacing(8)
        chunk_row.addWidget(speed_label)
        chunk_row.addWidget(self.speed_combo)

        box.addWidget(icon, 0, Qt.AlignHCenter)
        box.addSpacing(8)
        box.addWidget(drop_title, 0, Qt.AlignHCenter)
        box.addWidget(self.file_label, 0, Qt.AlignHCenter)
        box.addSpacing(6)
        file_buttons = QHBoxLayout()
        file_buttons.setAlignment(Qt.AlignCenter)
        file_buttons.setSpacing(12)
        file_buttons.addWidget(self.browse_btn)
        file_buttons.addWidget(self.clear_file_btn)
        box.addLayout(file_buttons)
        box.addSpacing(4)
        box.addWidget(self.info_label, 0, Qt.AlignHCenter)
        box.addWidget(self.progress, 0, Qt.AlignHCenter)
        box.addSpacing(4)
        box.addLayout(controls)
        box.addLayout(chunk_row)

        area.addStretch()
        area.addWidget(center, 0, Qt.AlignCenter)
        area.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(server_row)
        layout.addWidget(upload_area)
        layout.addWidget(self.create_chunk_status_panel())
        self.update_buttons()

    def create_chunk_status_panel(self):
        panel = QFrame()
        panel.setMinimumHeight(205)
        panel.setMaximumHeight(230)
        panel.setStyleSheet(f"""
        QFrame {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:16px;
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)

        box = QVBoxLayout(panel)
        box.setContentsMargins(18, 12, 18, 12)
        box.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel("Chunk Status")
        title.setStyleSheet("font-size:17px; font-weight:900; color:white;")
        self.chunk_plan_label = QLabel("Chunks: 0  |  Uploaded: 0 / 0 chunks  |  Speed: --")
        self.chunk_plan_label.setStyleSheet("font-size:14px; color:#b5c7e8;")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.chunk_plan_label)
        box.addLayout(top)

        self.chunk_table = QTableWidget()
        self.chunk_table.setColumnCount(4)
        self.chunk_table.setHorizontalHeaderLabels(["Chunk", "Size", "Status", "Progress"])
        self.chunk_table.verticalHeader().setVisible(False)
        self.chunk_table.setShowGrid(False)
        self.chunk_table.setMinimumHeight(145)
        self.chunk_table.setStyleSheet(f"""
        QTableWidget {{
            background:#0f1020;
            color:white;
            border:1px solid #26324a;
            border-radius:10px;
            gridline-color:transparent;
        }}
        QHeaderView::section {{
            background:#15172b;
            color:#b5c7e8;
            border:none;
            padding:8px;
            font-weight:bold;
        }}
        QTableWidget::item {{
            border:none;
            padding:6px;
        }}
        """)
        self.chunk_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.chunk_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.chunk_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.chunk_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        box.addWidget(self.chunk_table)
        return panel

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

        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        if size <= 0:
            self.clear_selected_file()
            QMessageBox.warning(self, "UPLOWER", EMPTY_FILE_MESSAGE)
            return

        self.selected_file = file_path
        self.file_label.setText(filename)
        self.info_label.setText(f"File: {filename}  |  Dung lượng: {self.format_bytes(size)}  |  Trạng thái: Sẵn sàng")
        self.progress.setValue(0)
        self.refresh_chunk_plan()
        self.update_buttons()

    def clear_selected_file(self):
        if self.upload_state != "stopped":
            QMessageBox.warning(self, "UPLOWER", "Không thể xóa file đã chọn khi đang upload.")
            return

        self.selected_file = None
        self.last_upload_file_path = ""
        self.last_upload_file_size = 0
        self.current_chunk_ranges = []
        self.file_label.setText("Chưa chọn file nào")
        self.info_label.setText("File: Chưa chọn file  |  Dung lượng: 0 MB  |  Trạng thái: Sẵn sàng")
        self.progress.setValue(0)
        if hasattr(self, "chunk_table"):
            self.chunk_table.setRowCount(0)
        if hasattr(self, "chunk_plan_label"):
            self.chunk_plan_label.setText("Chunks: 0  |  Uploaded: 0 / 0 chunks  |  Speed: --")
        self.update_buttons()

    def selected_chunk_size(self):
        return CHUNK_SIZE_OPTIONS.get(self.chunk_size_combo.currentText(), 5 * 1024 * 1024)

    def selected_thread_count(self):
        return THREAD_OPTIONS.get(self.thread_combo.currentText(), 1)

    def selected_duplicate_policy(self):
        return DEFAULT_DUPLICATE_POLICY

    def refresh_chunk_plan(self, *_args):
        if not hasattr(self, "chunk_table"):
            return
        if self.upload_state != "stopped":
            return
        if not self.selected_file or not os.path.isfile(self.selected_file):
            self.current_chunk_ranges = []
            self.chunk_table.setRowCount(0)
            self.chunk_plan_label.setText("Chunks: 0  |  Uploaded: 0 / 0 chunks  |  Speed: --")
            return

        file_size = os.path.getsize(self.selected_file)
        try:
            self.current_chunk_ranges = self.build_chunk_ranges(file_size, self.selected_chunk_size())
        except ValueError as e:
            self.current_chunk_ranges = []
            self.chunk_table.setRowCount(0)
            self.chunk_plan_label.setText(str(e))
            return
        self.populate_chunk_table(self.current_chunk_ranges)
        total_chunks = len(self.current_chunk_ranges)
        self.chunk_plan_label.setText(f"Chunks: {total_chunks}  |  Uploaded: 0 / {total_chunks} chunks  |  Speed: --")

    def populate_chunk_table(self, chunk_ranges):
        visible_rows = min(len(chunk_ranges), MAX_VISIBLE_CHUNK_ROWS)
        self.chunk_table.setRowCount(visible_rows)
        for row, (index, _offset, size) in enumerate(chunk_ranges[:visible_rows]):
            self.chunk_table.setItem(row, 0, QTableWidgetItem(f"#{index + 1}"))
            self.chunk_table.setItem(row, 1, QTableWidgetItem(self.format_bytes(size)))
            self.chunk_table.setItem(row, 2, QTableWidgetItem("Waiting"))
            self.chunk_table.setItem(row, 3, QTableWidgetItem("0%"))
            self.chunk_table.setRowHeight(row, 28)
        if len(chunk_ranges) > MAX_VISIBLE_CHUNK_ROWS:
            last_row = visible_rows - 1
            hidden = len(chunk_ranges) - MAX_VISIBLE_CHUNK_ROWS + 1
            self.chunk_table.setItem(last_row, 0, QTableWidgetItem("..."))
            self.chunk_table.setItem(last_row, 1, QTableWidgetItem(f"+{hidden} chunks"))
            self.chunk_table.setItem(last_row, 2, QTableWidgetItem("Hidden"))
            self.chunk_table.setItem(last_row, 3, QTableWidgetItem("--"))

    def update_chunk_status(self, index, status, progress):
        if not hasattr(self, "chunk_table"):
            return
        if 0 <= index < self.chunk_table.rowCount():
            self.chunk_table.setItem(index, 2, QTableWidgetItem(status))
            self.chunk_table.setItem(index, 3, QTableWidgetItem(f"{progress}%"))

    def update_chunk_summary(self, uploaded_chunks, total_chunks, speed_text):
        self.chunk_plan_label.setText(
            f"Chunks: {total_chunks}  |  Uploaded: {uploaded_chunks} / {total_chunks} chunks  |  Speed: {speed_text}"
        )

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
            self.show_no_file_warning()
            return
        if not os.path.isfile(self.selected_file) or os.path.getsize(self.selected_file) <= 0:
            QMessageBox.warning(self, "UPLOWER", EMPTY_FILE_MESSAGE)
            self.clear_selected_file()
            return
        if not self.probe_server_connection():
            self.set_server_status(False, f"Server: Chưa kết nối {self.server_host}:{self.server_port}")
            QMessageBox.warning(self, "UPLOWER", "Server chưa sẵn sàng. Vui lòng bật Server bên Admin rồi thử lại.")
            return
        self.set_server_status(True, f"Server: Đã kết nối {self.server_host}:{self.server_port}")
        if self.upload_state == "uploading":
            return
        self.refresh_chunk_plan()
        self.upload_state = "uploading"
        self.update_buttons()
        self.upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        self.upload_thread.start()

    def pause_upload(self):
        if not self.selected_file:
            self.show_no_file_warning()
            return

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
        if not self.selected_file:
            self.show_no_file_warning()
            return

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
        if not self.selected_file:
            self.show_no_file_warning()
            return

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
        thread_count = self.selected_thread_count()

        if file_size > 0:
            self.upload_worker_multipart(
                file_path,
                file_size,
                file_name,
                start_time,
                server_text,
                thread_count,
                self.selected_chunk_size(),
            )
            return

        try:
            self.socket_client = SocketClient(self.server_host, self.server_port)
            sock = self.socket_client.connect()
            manager = UploadManager(sock)
            offset = manager.prepare_upload(file_path, target_dir="", duplicate_policy=self.selected_duplicate_policy())

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
                message = self.upload_failure_message(e)
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Failed",
                    message=message,
                    user_email=self.user_email,
                    user_name=self.user_name,
                )

                # THÊM: upload lỗi thì lưu log vào SQL Server
                if save_upload_log:
                    try:
                        save_upload_log(
                            user_email=self.user_email,
                            action="upload_failed",
                            description=f"Upload thất bại {file_name}: {message}"
                        )
                    except Exception as log_error:
                        print("SQL Server log failed error:", log_error)

            self.finished_signal.emit(False, self.upload_failure_message(e))
        finally:
            if self.socket_client:
                self.socket_client.close()
                self.socket_client = None
            if self.upload_state != "paused":
                self.upload_state = "stopped"

    def upload_worker_multipart(self, file_path, file_size, file_name, start_time, server_text, thread_count, chunk_size):
        chunk_ranges = self.build_chunk_ranges(file_size, chunk_size)
        total_chunks = len(chunk_ranges)
        worker_count = max(1, min(thread_count, total_chunks))
        speed_limit = SPEED_LIMITS.get(self.speed_combo.currentText(), 0)
        per_worker_limit = int(speed_limit / worker_count) if speed_limit > 0 else 0

        chunk_queue = queue.Queue()
        for item in chunk_ranges:
            chunk_queue.put(item)

        sent_by_chunk = [0] * total_chunks
        completed_chunks = set()
        progress_lock = threading.Lock()
        errors = []
        cancel_event = threading.Event()
        progress_state = {"last_time": time.time(), "last_sent": 0}
        session_id = None

        try:
            self.chunk_summary_signal.emit(0, total_chunks, "--")
            init_client = SocketClient(self.server_host, self.server_port)
            self.socket_client = init_client
            init_sock = init_client.connect()
            init_manager = UploadManager(init_sock)
            session_id = init_manager.prepare_multipart_upload(
                file_path,
                target_dir="",
                duplicate_policy=self.selected_duplicate_policy(),
                part_count=total_chunks,
            )
            init_client.close()
            self.socket_client = None

            if not session_id:
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Skipped",
                    message="File already existed on server",
                    user_email=self.user_email,
                    user_name=self.user_name,
                )
                if save_upload_log:
                    try:
                        save_upload_log(
                            user_email=self.user_email,
                            action="upload_skipped",
                            description=f"File đã tồn tại trên server: {file_name}"
                        )
                    except Exception as e:
                        print("SQL Server log skipped error:", e)
                for index in range(min(total_chunks, MAX_VISIBLE_CHUNK_ROWS)):
                    self.chunk_status_signal.emit(index, "Skipped", 100)
                self.chunk_summary_signal.emit(0, total_chunks, "Skipped")
                self.progress_signal.emit(100, f"File: {file_name}  |  Dung lượng: {self.format_bytes(file_size)}  |  Trạng thái: Skipped")
                self.finished_signal.emit(True, "File đã có trên server và đã được xác minh.")
                return

            def emit_overall_progress():
                total_sent = sum(sent_by_chunk)
                now = time.time()
                if now - progress_state["last_time"] < 0.25 and total_sent < file_size:
                    return
                delta = total_sent - progress_state["last_sent"]
                speed = delta / max(now - progress_state["last_time"], 0.001)
                progress_state["last_time"] = now
                progress_state["last_sent"] = total_sent
                speed_text = f"{self.format_bytes(speed)}/s"
                uploaded_chunks = len(completed_chunks)
                percent = int(total_sent * 100 / file_size) if file_size else 100
                self.chunk_summary_signal.emit(uploaded_chunks, total_chunks, speed_text)
                self.progress_signal.emit(
                    percent,
                    f"File: {file_name}  |  {uploaded_chunks}/{total_chunks} chunks  |  "
                    f"Multi-chunk {worker_count} threads: {percent}%  |  Tốc độ: {speed_text}"
                )

            def on_chunk_progress(chunk_index, sent_in_chunk, _delta):
                progress = int(sent_in_chunk * 100 / chunk_ranges[chunk_index][2]) if chunk_ranges[chunk_index][2] else 100
                self.chunk_status_signal.emit(chunk_index, "Uploading", progress)
                with progress_lock:
                    sent_by_chunk[chunk_index] = sent_in_chunk
                    emit_overall_progress()

            def upload_worker_thread():
                while not cancel_event.is_set() and self.upload_state != "stopped":
                    try:
                        chunk_index, offset, size = chunk_queue.get_nowait()
                    except queue.Empty:
                        return

                    self.chunk_status_signal.emit(chunk_index, "Uploading", 0)
                    part_client = SocketClient(self.server_host, self.server_port)
                    try:
                        sock = part_client.connect()
                        manager = UploadManager(sock)
                        ok = manager.upload_multipart_part(
                            file_path,
                            session_id,
                            chunk_index,
                            offset,
                            size,
                            on_chunk=on_chunk_progress,
                            should_stop=lambda: self.upload_state == "stopped" or cancel_event.is_set(),
                            should_pause=lambda: self.upload_state == "paused",
                            speed_limit=per_worker_limit,
                        )
                        if ok:
                            with progress_lock:
                                sent_by_chunk[chunk_index] = size
                                completed_chunks.add(chunk_index)
                                emit_overall_progress()
                            self.chunk_status_signal.emit(chunk_index, "Complete", 100)
                        elif self.upload_state != "stopped":
                            errors.append(f"Chunk #{chunk_index + 1} gửi chưa hoàn tất.")
                            self.chunk_status_signal.emit(chunk_index, "Failed", 0)
                            cancel_event.set()
                    except Exception as e:
                        if self.upload_state != "stopped":
                            errors.append(f"Chunk #{chunk_index + 1}: {e}")
                            self.chunk_status_signal.emit(chunk_index, "Failed", 0)
                            cancel_event.set()
                    finally:
                        part_client.close()
                        chunk_queue.task_done()

            workers = [
                threading.Thread(target=upload_worker_thread, daemon=True)
                for _ in range(worker_count)
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join()

            if self.upload_state == "stopped":
                self.abort_multipart_session(session_id)
                add_upload_record(
                    file_path,
                    file_size,
                    server_text,
                    "Stopped",
                    message="Multi-chunk upload stopped by user",
                    user_email=self.user_email,
                    user_name=self.user_name,
                )
                self.finished_signal.emit(False, "Đã dừng upload multi-chunk.")
                return

            if errors:
                self.abort_multipart_session(session_id)
                if any(self.is_server_disconnect_error(error) for error in errors):
                    raise ConnectionError(SERVER_DISCONNECT_MESSAGE)
                raise RuntimeError("; ".join(errors[:3]))

            if len(completed_chunks) != total_chunks:
                self.abort_multipart_session(session_id)
                raise RuntimeError("Chưa upload đủ tất cả chunk.")

            finalize_client = SocketClient(self.server_host, self.server_port)
            self.socket_client = finalize_client
            finalize_sock = finalize_client.connect()
            finalize_manager = UploadManager(finalize_sock)
            finalize_manager.finalize_multipart_upload(session_id)
            finalize_client.close()
            self.socket_client = None

            elapsed = max(time.time() - start_time, 1)
            avg_speed = file_size / elapsed
            speed_text = f"{self.format_bytes(avg_speed)}/s"
            self.chunk_summary_signal.emit(total_chunks, total_chunks, speed_text)
            add_upload_record(
                file_path,
                file_size,
                server_text,
                "Verified",
                speed=speed_text,
                user_email=self.user_email,
                user_name=self.user_name,
            )

            if save_uploaded_file or save_upload_log:
                try:
                    file_hash = ""
                    try:
                        file_hash = UploadManager(None).calculate_file_hash(file_path)
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
                            description=f"Upload multi-chunk thành công {file_name}"
                        )
                except Exception as e:
                    print("SQL Server save multi-chunk upload error:", e)

            self.progress_signal.emit(
                100,
                f"File: {file_name}  |  Dung lượng: {self.format_bytes(file_size)}  |  "
                f"Multi-chunk Verified  |  {total_chunks}/{total_chunks} chunks  |  Trung bình: {speed_text}"
            )
            self.finished_signal.emit(True, "Upload multi-chunk thành công và checksum đã khớp.")

        except Exception as e:
            if session_id and self.upload_state != "stopped":
                self.abort_multipart_session(session_id)
            if self.upload_state == "stopped":
                status = "Stopped"
                message = "Multi-chunk upload stopped by user"
            else:
                status = "Failed"
                message = self.upload_failure_message(e, multipart=True)
                if save_upload_log:
                    try:
                        save_upload_log(
                            user_email=self.user_email,
                            action="upload_failed",
                            description=f"Upload multi-chunk thất bại {file_name}: {message}"
                        )
                    except Exception as log_error:
                        print("SQL Server log multi-chunk failed error:", log_error)

            add_upload_record(
                file_path,
                file_size,
                server_text,
                status,
                message=message,
                user_email=self.user_email,
                user_name=self.user_name,
            )
            self.finished_signal.emit(False, message)
        finally:
            if self.socket_client:
                self.socket_client.close()
                self.socket_client = None
            if self.upload_state != "paused":
                self.upload_state = "stopped"

    def abort_multipart_session(self, session_id):
        if not session_id:
            return
        abort_client = SocketClient(self.server_host, self.server_port, timeout=3)
        try:
            sock = abort_client.connect()
            manager = UploadManager(sock)
            manager.abort_multipart_upload(session_id)
        except Exception as e:
            if self.is_server_disconnect_error(e):
                print("Không thể hủy phiên upload vì Server đã ngắt kết nối.")
            else:
                print("Abort multi-chunk upload error:", e)
        finally:
            abort_client.close()

    def build_chunk_ranges(self, file_size, chunk_size):
        chunk_size = max(1, int(chunk_size or 1))
        chunk_count = max(1, (file_size + chunk_size - 1) // chunk_size)
        if chunk_count > 65535:
            raise ValueError("Số chunk vượt giới hạn 65535. Hãy chọn Chunk Size lớn hơn.")
        offset = 0
        ranges = []
        for index in range(chunk_count):
            size = min(chunk_size, file_size - offset)
            ranges.append((index, offset, size))
            offset += size
        return ranges

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

    def show_no_file_warning(self):
        QMessageBox.warning(self, "UPLOWER", "Vui lòng chọn file trước khi thao tác.")

    def update_buttons(self):
        has_file = self.selected_file is not None
        no_file_idle = not has_file and self.upload_state == "stopped"
        self.start_btn.setEnabled(no_file_idle or (has_file and self.upload_state == "stopped"))
        self.pause_btn.setEnabled(no_file_idle or self.upload_state == "uploading")
        self.resume_btn.setEnabled(no_file_idle or self.upload_state == "paused")
        self.stop_btn.setEnabled(no_file_idle or self.upload_state in ("uploading", "paused"))
        self.browse_btn.setEnabled(self.upload_state == "stopped")
        if hasattr(self, "clear_file_btn"):
            self.clear_file_btn.setEnabled(has_file and self.upload_state == "stopped")
        self.chunk_size_combo.setEnabled(self.upload_state == "stopped")
        self.thread_combo.setEnabled(self.upload_state == "stopped")
        self.speed_combo.setEnabled(self.upload_state == "stopped")
        if hasattr(self, "check_server_btn"):
            self.check_server_btn.setEnabled(self.upload_state == "stopped")

    def format_bytes(self, value):
        value = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024
