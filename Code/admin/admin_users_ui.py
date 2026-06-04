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


USER_TABLE_HEADERS = ["User", "Email", "Role", "Status"]
SAMPLE_USERS = [
    ["User 1", "user1@gmail.com", "User", "Online"],
    ["User 2", "user2@gmail.com", "User", "Offline"],
    ["User 3", "user3@gmail.com", "User", "Online"],
    ["User 4", "user4@gmail.com", "User", "Offline"],
    ["User 5", "user5@gmail.com", "User", "Online"],
    ["Admin", "admin@gmail.com", "Admin", "Online"],
]


class AdminUsersUI(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(18)

        title = QLabel("User Management")
        title.setStyleSheet(self.title_style())

        layout.addWidget(title)

        top = QHBoxLayout()

        add_btn = QPushButton("Thêm User")
        lock_btn = QPushButton("Khóa tài khoản")

        self.apply_button_style(add_btn, lock_btn)

        top.addWidget(add_btn)
        top.addWidget(lock_btn)
        top.addStretch()

        layout.addLayout(top)

        table = QTableWidget(len(SAMPLE_USERS), len(USER_TABLE_HEADERS))

        table.setHorizontalHeaderLabels(USER_TABLE_HEADERS)

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

        self.fill_table(table, SAMPLE_USERS)

        layout.addWidget(table)
        layout.addStretch()

    def title_style(self):
        return f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
        """

    def fill_table(self, table, rows):
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table.setItem(row_index, col_index, QTableWidgetItem(value))

    def apply_button_style(self, *buttons):
        for button in buttons:
            button.setStyleSheet(BUTTON_STYLE)
