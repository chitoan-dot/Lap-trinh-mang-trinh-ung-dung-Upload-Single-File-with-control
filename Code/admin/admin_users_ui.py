from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton
)

from layout.theme import *
from layout.style import *


class AdminUsersUI(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(18)

        title = QLabel("User Management")
        title.setStyleSheet(f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
        """)

        layout.addWidget(title)

        top = QHBoxLayout()

        add_btn = QPushButton("Thêm User")
        lock_btn = QPushButton("Khóa tài khoản")

        add_btn.setStyleSheet(BUTTON_STYLE)
        lock_btn.setStyleSheet(BUTTON_STYLE)

        top.addWidget(add_btn)
        top.addWidget(lock_btn)
        top.addStretch()

        layout.addLayout(top)

        table = QTableWidget(6, 4)

        table.setHorizontalHeaderLabels([
            "User",
            "Email",
            "Role",
            "Status"
        ])

        table.horizontalHeader().setStretchLastSection(True)

        table.setStyleSheet(f"""
        QTableWidget {{
            background:{CARD};
            color:{TEXT};
            border:1px solid {BORDER};
            border-radius:16px;
            gridline-color:{BORDER};
        }}

        QHeaderView::section {{
            background:{INPUT};
            color:{TEXT};
            padding:10px;
            border:none;
            font-weight:bold;
        }}
        """)

        data = [
            ["User 1", "user1@gmail.com", "User", "Online"],
            ["User 2", "user2@gmail.com", "User", "Offline"],
            ["User 3", "user3@gmail.com", "User", "Online"],
            ["User 4", "user4@gmail.com", "User", "Offline"],
            ["User 5", "user5@gmail.com", "User", "Online"],
            ["Admin", "admin@gmail.com", "Admin", "Online"],
        ]

        for r, row in enumerate(data):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(value))

        layout.addWidget(table)
        layout.addStretch()