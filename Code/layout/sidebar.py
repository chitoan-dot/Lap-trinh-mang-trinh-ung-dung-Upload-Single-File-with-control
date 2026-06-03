from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QPushButton
)

from PyQt5.QtCore import pyqtSignal

from layout.theme import *


class Sidebar(QFrame):

    page_changed = pyqtSignal(str)

    def __init__(self, role="user"):
        super().__init__()

        self.setFixedWidth(260)

        self.setStyleSheet(f"""
        QFrame {{

            background:{CARD};

            border-right:1px solid {BORDER};

        }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            25,
            20,
            25
        )

        layout.setSpacing(14)

        title = QLabel(
            "☁ UPLOWER"
        )

        title.setStyleSheet(f"""

            color:{PINK};

            font-size:24px;

            font-weight:bold;

        """)

        sub = QLabel(

            "Admin Portal"

            if role == "admin"

            else

            "User Portal"

        )

        sub.setStyleSheet(f"""

            color:{TEXT2};

            font-size:13px;

        """)

        layout.addWidget(title)
        layout.addWidget(sub)

        layout.addSpacing(20)

        self.buttons = {}

        if role == "admin":

            items = [

                ("dashboard","📊 Dashboard"),

                ("users","👥 Users"),

                ("files","📁 Files"),

                ("analytics","📈 Analytics"),

                ("security","🛡 Security"),

                ("server","🖥 Server"),

                ("profile","👤 Profile")

            ]

        else:

            items = [

                ("dashboard","📊 Dashboard"),

                ("upload","⬆ Upload"),

                ("files","📁 My Files"),

                ("statistics","📈 Statistics"),

                ("profile","👤 Profile"),

                ("settings","⚙ Settings")

            ]

        for key,text in items:

            btn = QPushButton(text)

            btn.clicked.connect(

                lambda _,k=key:

                self.page_changed.emit(k)

            )

            btn.setStyleSheet(f"""

            QPushButton {{

                background:transparent;

                color:{TEXT2};

                border:none;

                text-align:left;

                padding:14px;

                border-radius:12px;

                font-size:15px;

                font-weight:600;

            }}

            QPushButton:hover {{

                background:#2B1248;

                color:{TEXT};

            }}

            """)

            layout.addWidget(btn)

            self.buttons[key] = btn

        layout.addStretch()

        logout = QLabel(
            "© 2026 UPLOWER"
        )

        logout.setStyleSheet(

            f"color:{TEXT2};"

        )

        layout.addWidget(logout)

        self.set_active(
            "dashboard"
        )

    def set_active(self,key):

        for name,btn in self.buttons.items():

            if name == key:

                btn.setStyleSheet(f"""

                QPushButton {{

                    background:{GRADIENT};

                    color:white;

                    border:none;

                    padding:14px;

                    border-radius:12px;

                    font-size:15px;

                    font-weight:bold;

                    text-align:left;

                }}

                """)

            else:

                btn.setStyleSheet(f"""

                QPushButton {{

                    background:transparent;

                    color:{TEXT2};

                    border:none;

                    padding:14px;

                    border-radius:12px;

                    text-align:left;

                }}

                QPushButton:hover {{

                    background:#2B1248;

                    color:{TEXT};

                }}

                """)