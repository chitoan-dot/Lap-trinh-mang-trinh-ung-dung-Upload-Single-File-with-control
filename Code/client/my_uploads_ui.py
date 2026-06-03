import os

from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.upload_history import clear_upload_history, load_upload_history
from layout.theme import *
from layout.style import PAGE_STYLE


class MyUploadsUI(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.user_email = str(self.current_user.get("email", "")).strip().lower()
        self.records = []
        self.setStyleSheet(PAGE_STYLE)
        self.build_ui()
        self.refresh_history()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(24)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Lịch sử upload")
        title.setStyleSheet("font-size:36px; font-weight:900; border:none;")
        subtitle = QLabel("Lịch sử các lần gửi file của tài khoản hiện tại")
        subtitle.setStyleSheet(f"font-size:19px; color:{TEXT2}; border:none;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        refresh_btn = QPushButton("Làm mới")
        refresh_btn.setFixedSize(120, 46)
        refresh_btn.setStyleSheet(self.button_style())
        refresh_btn.clicked.connect(self.refresh_history)

        clear_btn = QPushButton("Xóa lịch sử")
        clear_btn.setFixedSize(130, 46)
        clear_btn.setStyleSheet(self.button_style())
        clear_btn.clicked.connect(self.clear_history)

        top.addLayout(title_box)
        top.addStretch()
        top.addWidget(refresh_btn)
        top.addWidget(clear_btn)
        layout.addLayout(top)

        stats = QHBoxLayout()
        stats.setSpacing(18)
        self.total_card = self.stat_card("Tổng lượt gửi", "0")
        self.success_card = self.stat_card("Đã upload", "0")
        self.skipped_card = self.stat_card("Đã có sẵn", "0")
        self.failed_card = self.stat_card("Lỗi/Dừng", "0")
        self.size_card = self.stat_card("Dung lượng mới", "0 MB")
        for card in (self.total_card, self.success_card, self.skipped_card, self.failed_card, self.size_card):
            stats.addWidget(card)
        layout.addLayout(stats)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Thời gian", "Tệp", "Dung lượng", "Server", "Tốc độ", "Trạng thái", "Mở"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(430)
        self.table.setStyleSheet(self.table_style())
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for index in range(2, 6):
            self.table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 96)
        layout.addWidget(self.table, 1)

    def refresh_history(self):
        self.records = load_upload_history(self.user_email)
        self.table.setRowCount(0)

        for row, record in enumerate(self.records):
            self.table.insertRow(row)
            values = [
                record.get("time", ""),
                record.get("file_name", ""),
                self.format_bytes(record.get("file_size", 0)),
                record.get("server", ""),
                record.get("speed", ""),
                record.get("status", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

            open_btn = QPushButton("Mở")
            open_btn.setFixedSize(72, 30)
            open_btn.setEnabled(os.path.exists(record.get("file_path", "")))
            open_btn.setStyleSheet(self.open_button_style())
            open_btn.clicked.connect(lambda _checked=False, idx=row: self.open_local_file(idx))
            self.table.setCellWidget(row, 6, open_btn)
            self.table.setRowHeight(row, 42)

        total = len(self.records)
        success = sum(1 for r in self.records if r.get("status") == "Verified")
        skipped = sum(1 for r in self.records if r.get("status") == "Skipped")
        failed = total - success - skipped
        total_size = sum(int(r.get("file_size", 0) or 0) for r in self.records if r.get("status") == "Verified")
        self.total_card.value_label.setText(str(total))
        self.success_card.value_label.setText(str(success))
        self.skipped_card.value_label.setText(str(skipped))
        self.failed_card.value_label.setText(str(failed))
        self.size_card.value_label.setText(self.format_bytes(total_size))

    def clear_history(self):
        clear_upload_history(self.user_email)
        self.refresh_history()

    def open_local_file(self, index):
        if index < 0 or index >= len(self.records):
            return
        file_path = self.records[index].get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "UPLOWER", "Không tìm thấy file gốc trên máy client.")
            return
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "UPLOWER", f"Không thể mở file: {e}")

    def stat_card(self, title, value):
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(22, 16, 22, 16)
        box.setSpacing(8)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:28px; font-weight:900; color:white; border:none;")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size:15px; color:{TEXT2}; border:none;")

        box.addWidget(value_label)
        box.addWidget(title_label)
        card.value_label = value_label
        return card

    def card_style(self):
        return f"""
        QFrame {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        QFrame:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        """

    def button_style(self):
        return f"""
        QPushButton {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:12px;
            font-size:15px;
            font-weight:bold;
            padding:8px 12px;
        }}
        QPushButton:hover {{ border:1px solid {PRIMARY}; background:#171832; }}
        QPushButton:pressed {{ background:#30174f; }}
        QPushButton:disabled {{ color:#64748b; border:1px solid #26324a; }}
        """

    def open_button_style(self):
        return f"""
        QPushButton {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:8px;
            font-size:14px;
            font-weight:bold;
            padding:0px;
        }}
        QPushButton:hover {{ border:1px solid {PRIMARY}; background:#171832; }}
        QPushButton:pressed {{ background:#30174f; }}
        QPushButton:disabled {{ color:#64748b; border:1px solid #26324a; }}
        """

    def table_style(self):
        return f"""
        QTableWidget {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
            color:white;
            font-size:15px;
            gridline-color:transparent;
        }}
        QHeaderView::section {{
            background:#13162a;
            color:#b5c7e8;
            border:none;
            padding:12px;
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
        """

    def format_bytes(self, value):
        value = float(value or 0)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024
