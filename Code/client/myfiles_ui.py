from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout
)

from layout.theme import *
from layout.style import *


class MyFilesUI(QWidget):

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

        layout.setSpacing(18)

        title = QLabel("File của tôi")

        title.setStyleSheet(
            f"""
            font-size:26px;
            font-weight:bold;
            color:{TEXT};
            """
        )

        layout.addWidget(title)

        top = QHBoxLayout()

        all_btn = QPushButton("Tất cả")
        upload_btn = QPushButton("Đang Upload")
        done_btn = QPushButton("Hoàn tất")

        for btn in [
            all_btn,
            upload_btn,
            done_btn
        ]:

            btn.setStyleSheet(
                BUTTON_STYLE
            )

            top.addWidget(btn)

        top.addStretch()

        layout.addLayout(top)

        table = QTableWidget(5,5)

        table.setHorizontalHeaderLabels([

            "Tên file",
            "Dung lượng",
            "Trạng thái",
            "Ngày tải",
            "Hành động"

        ])

        table.horizontalHeader().setStretchLastSection(
            True
        )

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

            (
                "report.pdf",
                "2.4 MB",
                "Hoàn tất",
                "26/05/2026",
                "Tải xuống"
            ),

            (
                "video.mp4",
                "128 MB",
                "Đang upload",
                "26/05/2026",
                "Pause"
            ),

            (
                "source.zip",
                "45 MB",
                "Đã tạm dừng",
                "25/05/2026",
                "Resume"
            ),

            (
                "image.png",
                "4 MB",
                "Hoàn tất",
                "24/05/2026",
                "Xóa"
            ),

            (
                "data.xlsx",
                "1 MB",
                "Hoàn tất",
                "24/05/2026",
                "Mở"
            )

        ]

        for r,row in enumerate(data):

            for c,value in enumerate(row):

                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(value)
                )

        layout.addWidget(table)
        layout.addStretch()
