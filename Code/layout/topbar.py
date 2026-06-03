from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton
)

from layout.theme import *


class Topbar(QFrame):

    def __init__(
        self,
        title="Dashboard",
        role="User"
    ):

        super().__init__()

        self.setFixedHeight(70)

        self.setStyleSheet(f"""
        QFrame {{

            background:{BG};

            border-bottom:1px solid {BORDER};

        }}
        """)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            24,
            0,
            24,
            0
        )

        self.title = QLabel(title)

        self.title.setStyleSheet(f"""

            color:{TEXT};

            font-size:24px;

            font-weight:bold;

        """)

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Tìm kiếm..."
        )

        self.search.setFixedWidth(
            260
        )

        self.search.setStyleSheet(f"""

        QLineEdit {{

            background:{INPUT};

            color:{TEXT};

            border:1px solid {BORDER};

            border-radius:10px;

            padding:8px;

        }}

        """)

        notify = QPushButton("🔔")

        notify.setFixedSize(
            40,
            40
        )

        notify.setStyleSheet(f"""

        QPushButton {{

            background:{CARD};

            border:1px solid {BORDER};

            border-radius:12px;

        }}

        """)

        user = QLabel(
            f"👤 {role}"
        )

        user.setStyleSheet(f"""

            color:{TEXT2};

            font-size:14px;

        """)

        layout.addWidget(
            self.title
        )

        layout.addStretch()

        layout.addWidget(
            self.search
        )

        layout.addWidget(
            notify
        )

        layout.addWidget(
            user
        )

    def set_title(
        self,
        title
    ):

        self.title.setText(
            title.title()
        )