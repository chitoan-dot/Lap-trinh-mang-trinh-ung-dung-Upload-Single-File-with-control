from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from widgets.stat_card import StatCard
from layout.theme import *
from layout.style import *


class AdminAnalyticsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)

        title = QLabel("Admin Analytics")
        title.setStyleSheet(f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
        """)
        layout.addWidget(title)

        # Stat cards
        row = QHBoxLayout()
        row.setSpacing(15)

        cards = [
            StatCard("Traffic", "2.4 TB", "🌐", "+14%"),
            StatCard("Requests", "148k", "📡", "Today"),
            StatCard("Errors", "37", "⚠", "-8%"),
        ]

        for card in cards:
            row.addWidget(card)

        layout.addLayout(row)

        # Analytics card
        analytics_card = QFrame()
        analytics_card.setStyleSheet(CARD_STYLE)

        box = QVBoxLayout(analytics_card)
        box.setContentsMargins(25, 25, 25, 25)
        box.setSpacing(18)

        subtitle = QLabel("📊 Server Analytics")
        subtitle.setStyleSheet(f"""
            color:{TEXT};
            font-size:20px;
            font-weight:bold;
        """)
        box.addWidget(subtitle)

        items = [
            ("Upload", 72),
            ("Download", 48),
            ("Storage", 64),
            ("Security", 12),
        ]

        for name, value in items:
            label = QLabel(f"{name}: {value}%")
            label.setStyleSheet(f"""
                color:{TEXT};
                font-size:16px;
                font-weight:bold;
            """)

            bar = QProgressBar()
            bar.setValue(value)
            bar.setTextVisible(True)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background:{INPUT};
                    border:1px solid {BORDER};
                    border-radius:10px;
                    color:white;
                    text-align:center;
                    height:20px;
                }}

                QProgressBar::chunk {{
                    background:{GRADIENT};
                    border-radius:10px;
                }}
            """)

            box.addWidget(label)
            box.addWidget(bar)

        layout.addWidget(analytics_card)
        layout.addStretch()