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


class AdminFilesUI(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35,35,35,35)
        layout.setSpacing(18)

        title = QLabel("File Management")
        title.setStyleSheet(f"""
            font-size:28px;
            font-weight:bold;
            color:{TEXT};
        """)

        layout.addWidget(title)

        top = QHBoxLayout()

        scan_btn = QPushButton("Quét file lỗi")
        clear_btn = QPushButton("Xóa Cache")

        scan_btn.setStyleSheet(BUTTON_STYLE)
        clear_btn.setStyleSheet(BUTTON_STYLE)

        top.addWidget(scan_btn)
        top.addWidget(clear_btn)
        top.addStretch()

        layout.addLayout(top)

        table = QTableWidget(5,6)

        table.setHorizontalHeaderLabels([
            "File",
            "Owner",
            "Size",
            "Status",
            "Upload Date",
            "Action"
        ])

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

        data = [

            ("backup.zip","user01","600MB","Completed","26/05","View"),

            ("video.mp4","user02","1.2GB","Uploading","26/05","Control"),

            ("secret.rar","user03","80MB","Blocked","25/05","Review"),

            ("doc.pdf","user04","3MB","Completed","24/05","View"),

            ("app.exe","user05","22MB","Warning","24/05","Scan")

        ]

        for r,row in enumerate(data):

            for c,value in enumerate(row):

                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(value)
                )

        layout.addWidget(table)