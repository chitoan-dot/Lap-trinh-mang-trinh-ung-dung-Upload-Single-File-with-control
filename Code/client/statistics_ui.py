from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame
)

from widgets.stat_card import StatCard
from layout.theme import *
from layout.style import *


class StatisticsUI(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(20)

        title = QLabel("Statistics")
        title.setStyleSheet(f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
        """)

        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(15)

        cards = [
            StatCard("Upload hôm nay", "24", "⬆", "+18%"),
            StatCard("Tốc độ TB", "8.2 MB/s", "⚡", "Ổn định"),
            StatCard("File lỗi", "2", "⚠", "Cần kiểm tra"),
        ]

        for card in cards:
            row.addWidget(card)

        layout.addLayout(row)

        chart = QFrame()
        chart.setStyleSheet(CARD_STYLE)

        chart_layout = QVBoxLayout(chart)
        chart_layout.setContentsMargins(25, 25, 25, 25)

        chart_title = QLabel("📈 Biểu đồ thống kê upload theo ngày")
        chart_title.setStyleSheet(f"""
            color:{TEXT};
            font-size:18px;
            font-weight:bold;
        """)

        chart_text = QLabel(
            "Mon  ███████  42%\n"
            "Tue  ██████████  65%\n"
            "Wed  █████  35%\n"
            "Thu  ████████████  82%\n"
            "Fri  ████████  56%"
        )
        chart_text.setStyleSheet(f"""
            color:{TEXT2};
            font-size:16px;
            line-height:1.6;
        """)

        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(chart_text)

        layout.addWidget(chart)
        layout.addStretch()