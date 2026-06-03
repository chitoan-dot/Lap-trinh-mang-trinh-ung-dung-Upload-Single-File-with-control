from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QHBoxLayout
)

from layout.theme import *
from layout.style import *


class SettingsUI(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            35,
            35,
            35,
            35
        )

        layout.setSpacing(20)

        title = QLabel("Settings")

        title.setStyleSheet(
            f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
            """
        )

        layout.addWidget(title)

        card = QFrame()

        card.setStyleSheet(
            CARD_STYLE
        )

        box = QVBoxLayout(card)

        box.setContentsMargins(
            30,
            30,
            30,
            30
        )

        box.setSpacing(16)

        options = [

            "Bật thông báo upload",

            "Tự động Resume khi mất kết nối",

            "Lưu lịch sử upload",

            "Bảo mật tài khoản",

            "Giao diện tối"

        ]

        self.checks = []

        for text in options:

            cb = QCheckBox(text)

            cb.setStyleSheet(f"""

            QCheckBox {{

                color:{TEXT};

                font-size:15px;

                spacing:10px;

            }}

            QCheckBox::indicator {{

                width:18px;

                height:18px;

            }}

            """)

            box.addWidget(cb)

            self.checks.append(cb)

        btns = QHBoxLayout()

        save = QPushButton(
            "Lưu Cài Đặt"
        )

        reset = QPushButton(
            "Khôi phục"
        )

        save.setStyleSheet(
            BUTTON_STYLE
        )

        reset.setStyleSheet(
            BUTTON_STYLE
        )

        save.clicked.connect(
            self.save_settings
        )

        reset.clicked.connect(
            self.reset_settings
        )

        btns.addWidget(save)
        btns.addWidget(reset)

        box.addLayout(btns)

        layout.addWidget(card)

        layout.addStretch()

    def save_settings(self):

        QMessageBox.information(

            self,

            "UPLOWER",

            "Đã lưu cài đặt"

        )

    def reset_settings(self):

        for cb in self.checks:

            cb.setChecked(False)