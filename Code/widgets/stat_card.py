from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from layout.theme import BORDER, CARD, CARD2, GREEN, PRIMARY, RED, TEXT, TEXT2


class StatCard(QFrame):
    def __init__(self, title, value, icon="", note=""):
        super().__init__()
        self.setMinimumHeight(150)
        self.setStyleSheet(f"""
        QFrame {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)

        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(46, 46)
        icon_label.setStyleSheet(f"""
        QLabel {{
            background:{CARD2};
            color:{PRIMARY};
            border-radius:14px;
            font-size:22px;
            font-weight:900;
        }}
        """)

        note_label = QLabel(note)
        note_color = RED if str(note).strip().startswith("-") else GREEN
        note_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        note_label.setStyleSheet(f"color:{note_color}; font-size:13px; font-weight:700;")

        top.addWidget(icon_label)
        top.addStretch()
        top.addWidget(note_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color:{TEXT}; font-size:26px; font-weight:900;")

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color:{TEXT2}; font-size:14px;")

        layout.addLayout(top)
        layout.addStretch()
        layout.addWidget(value_label)
        layout.addWidget(title_label)
