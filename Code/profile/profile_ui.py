from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QPushButton,
    QMessageBox
)

from layout.theme import *
from layout.style import *


class ProfileUI(QWidget):

    def __init__(self, role="user"):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 30, 30, 30)

        title = QLabel(
            "Hồ Sơ Quản Trị Viên" if role == "admin" else "Hồ Sơ Cá Nhân"
        )
        title.setStyleSheet(
            f"font-size:26px; font-weight:bold; color:{TEXT};"
        )

        grid = QGridLayout()
        grid.setSpacing(18)

        fields = [
            ("Họ và Tên", "Administrator" if role == "admin" else "User Demo"),
            ("Email", "admin@uplower.com" if role == "admin" else "user@uplower.com"),
            ("Số Điện Thoại", "+84 123 456 789"),
            ("Địa Chỉ", "Việt Nam"),
            ("Chức Vụ", "Admin" if role == "admin" else "User"),
            ("Phòng Ban", "System" if role == "admin" else "Client"),
        ]

        self.inputs = []

        for i, (label, value) in enumerate(fields):
            l = QLabel(label)
            l.setStyleSheet(f"color:{TEXT2}; font-weight:bold;")

            inp = QLineEdit(value)
            inp.setStyleSheet(INPUT_STYLE)

            grid.addWidget(l, i, 0)
            grid.addWidget(inp, i, 1)

            self.inputs.append(inp)

        save = QPushButton("Lưu Thay Đổi")
        save.setStyleSheet(BUTTON_STYLE)
        save.clicked.connect(self.save_profile)

        box.addWidget(title)
        box.addSpacing(20)
        box.addLayout(grid)
        box.addSpacing(20)
        box.addWidget(save)

        layout.addWidget(card)
        layout.addStretch()

    def save_profile(self):
        QMessageBox.information(
            self,
            "UPLOWER",
            "Đã lưu thông tin hồ sơ"
        )
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from layout.theme import *


class ProfileUI(QWidget):
    def __init__(self, role="user"):
        super().__init__()
        self.role = role
        self.setStyleSheet(f"background:{BG}; color:{TEXT};")

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 35, 40, 35)
        root.setSpacing(28)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Hồ Sơ Của Tôi")
        title.setStyleSheet("font-size:36px; font-weight:900;")

        sub = QLabel("Quản lý thông tin cá nhân và cài đặt tài khoản")
        sub.setStyleSheet(f"font-size:20px; color:{TEXT2};")

        title_box.addWidget(title)
        title_box.addWidget(sub)

        edit_btn = QPushButton("Chỉnh Sửa Hồ Sơ")
        edit_btn.setFixedSize(190, 52)
        edit_btn.setStyleSheet(f"""
        QPushButton {{
            background:{GRADIENT};
            color:white;
            border:none;
            border-radius:14px;
            font-size:17px;
            font-weight:bold;
        }}
        """)

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(edit_btn)

        root.addLayout(header)

        row1 = QHBoxLayout()
        row1.setSpacing(30)

        row1.addWidget(self.profile_card(), 1)
        row1.addWidget(self.personal_info_card(), 2)

        root.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(30)

        row2.addWidget(self.quick_stats_card(), 1)
        row2.addWidget(self.work_info_card(), 2)

        root.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(30)

        row3.addWidget(self.achievement_card(), 1)
        row3.addWidget(self.recent_activity_card(), 2)

        root.addLayout(row3)
        root.addStretch()

    def card_style(self):
        return f"""
        QFrame {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        """

    def input_style(self):
        return f"""
        QLineEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:16px;
            font-size:17px;
        }}
        """

    def profile_card(self):
        card = QFrame()
        card.setMinimumHeight(330)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setAlignment(Qt.AlignCenter)
        box.setSpacing(14)

        avatar = QLabel("♙")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(160, 160)
        avatar.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            border-radius:80px;
            font-size:80px;
            font-weight:bold;
        }}
        """)

        name = QLabel("Người dùng mới")
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("font-size:25px; font-weight:900;")

        role = QLabel("User")
        role.setAlignment(Qt.AlignCenter)
        role.setStyleSheet(f"font-size:17px; color:{TEXT2};")

        dept = QLabel("Chưa cập nhật")
        dept.setAlignment(Qt.AlignCenter)
        dept.setStyleSheet(f"font-size:15px; color:{TEXT2};")

        box.addWidget(avatar)
        box.addWidget(name)
        box.addWidget(role)
        box.addWidget(dept)

        return card

    def personal_info_card(self):
        card = QFrame()
        card.setMinimumHeight(330)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(18)

        title = QLabel("Thông Tin Cá Nhân")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)

        fields = [
            ("Họ và Tên", "Chưa cập nhật"),
            ("Email", "Chưa cập nhật"),
            ("Số Điện Thoại", "Chưa cập nhật"),
            ("Địa Chỉ", "Chưa cập nhật"),
        ]

        for i, (label, value) in enumerate(fields):
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size:16px; color:{TEXT2}; font-weight:bold;")

            inp = QLineEdit()
            inp.setText(value)
            inp.setReadOnly(True)
            inp.setFixedHeight(56)
            inp.setStyleSheet(self.input_style())

            grid.addWidget(lb, i // 2 * 2, i % 2)
            grid.addWidget(inp, i // 2 * 2 + 1, i % 2)

        box.addLayout(grid)
        box.addStretch()

        return card

    def quick_stats_card(self):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(16)

        title = QLabel("Thống Kê Nhanh")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        stats = [
            ("⇧", "Total Uploads", "0"),
            ("▤", "Total Files", "0"),
            ("▰", "Storage Used", "0 MB"),
            ("◷", "Account Age", "0 days"),
        ]

        for icon, name, value in stats:
            row = QFrame()
            row.setFixedHeight(60)
            row.setStyleSheet("background:#13162a; border:none; border-radius:14px;")

            r = QHBoxLayout(row)
            r.setContentsMargins(18, 0, 18, 0)

            ic = QLabel(icon)
            ic.setStyleSheet("font-size:24px; color:#c084fc;")

            lb = QLabel(name)
            lb.setStyleSheet(f"font-size:17px; color:{TEXT2};")

            val = QLabel(value)
            val.setStyleSheet("font-size:18px; font-weight:900;")

            r.addWidget(ic)
            r.addWidget(lb)
            r.addStretch()
            r.addWidget(val)

            box.addWidget(row)

        return card

    def work_info_card(self):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(18)

        title = QLabel("Thông Tin Công Việc")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)

        fields = [
            ("Chức Vụ", "Chưa cập nhật"),
            ("Phòng Ban", "Chưa cập nhật"),
        ]

        for i, (label, value) in enumerate(fields):
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size:16px; color:{TEXT2}; font-weight:bold;")

            inp = QLineEdit(value)
            inp.setReadOnly(True)
            inp.setFixedHeight(56)
            inp.setStyleSheet(self.input_style())

            grid.addWidget(lb, 0, i)
            grid.addWidget(inp, 1, i)

        about_lb = QLabel("Giới Thiệu Bản Thân")
        about_lb.setStyleSheet(f"font-size:16px; color:{TEXT2}; font-weight:bold;")

        about = QTextEdit()
        about.setReadOnly(True)
        about.setText("Chưa cập nhật")
        about.setFixedHeight(120)
        about.setStyleSheet(f"""
        QTextEdit {{
            background:{CARD2};
            color:{TEXT2};
            border:1px solid #334155;
            border-radius:14px;
            padding:14px;
            font-size:17px;
        }}
        """)

        box.addLayout(grid)
        box.addWidget(about_lb)
        box.addWidget(about)

        return card

    def achievement_card(self):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)

        title = QLabel("Thành Tích")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        empty = QLabel("Chưa có thành tích")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"font-size:18px; color:{TEXT2};")

        box.addStretch()
        box.addWidget(empty)
        box.addStretch()

        return card

    def recent_activity_card(self):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)

        title = QLabel("Hoạt Động Gần Đây")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        empty = QLabel("Chưa có hoạt động gần đây")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"font-size:18px; color:{TEXT2};")

        box.addStretch()
        box.addWidget(empty)
        box.addStretch()

        return card