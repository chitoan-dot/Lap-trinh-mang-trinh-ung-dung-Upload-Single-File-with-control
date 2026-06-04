from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from layout.theme import *


SIDEBAR_WIDTH = 260
DEFAULT_PAGE = "dashboard"

MENU_ITEMS = {
    "admin": [
        ("dashboard", "Dashboard"),
        ("users", "Users"),
        ("files", "Files"),
        ("analytics", "Analytics"),
        ("security", "Security"),
        ("server", "Server"),
        ("profile", "Profile"),
    ],
    "user": [
        ("dashboard", "Dashboard"),
        ("upload", "Upload"),
        ("files", "My Files"),
        ("statistics", "Statistics"),
        ("profile", "Profile"),
        ("settings", "Settings"),
    ],
}


class Sidebar(QFrame):
    page_changed = pyqtSignal(str)

    def __init__(self, role="user"):
        super().__init__()
        self.role = role if role in MENU_ITEMS else "user"
        self.buttons = {}

        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(self.sidebar_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(14)

        layout.addWidget(self.title_label())
        layout.addWidget(self.portal_label())
        layout.addSpacing(20)

        self.add_menu_buttons(layout)
        layout.addStretch()
        layout.addWidget(self.footer_label())

        self.set_active(DEFAULT_PAGE)

    def sidebar_style(self):
        return f"""
        QFrame {{
            background:{CARD};
            border-right:1px solid {BORDER};
        }}
        """

    def title_label(self):
        title = QLabel("UPLOWER")
        title.setStyleSheet(f"""
            color:{PINK};
            font-size:24px;
            font-weight:bold;
        """)
        return title

    def portal_label(self):
        text = "Admin Portal" if self.role == "admin" else "User Portal"
        label = QLabel(text)
        label.setStyleSheet(f"""
            color:{TEXT2};
            font-size:13px;
        """)
        return label

    def footer_label(self):
        footer = QLabel("2026 UPLOWER")
        footer.setStyleSheet(f"color:{TEXT2};")
        return footer

    def add_menu_buttons(self, layout):
        for key, text in MENU_ITEMS[self.role]:
            button = self.nav_button(key, text)
            layout.addWidget(button)
            self.buttons[key] = button

    def nav_button(self, key, text):
        button = QPushButton(text)
        button.clicked.connect(lambda _checked=False, page=key: self.page_changed.emit(page))
        button.setStyleSheet(self.normal_button_style())
        return button

    def normal_button_style(self):
        return f"""
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
        """

    def active_button_style(self):
        return f"""
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
        """

    def set_active(self, key):
        for name, button in self.buttons.items():
            style = self.active_button_style() if name == key else self.normal_button_style()
            button.setStyleSheet(style)
