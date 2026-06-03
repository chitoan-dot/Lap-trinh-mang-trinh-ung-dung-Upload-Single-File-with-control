from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from layout.theme import *
from client.my_uploads_ui import MyUploadsUI
from client.upload_ui import UploadUI
from profile.profile_ui import ProfileUI


class ClientUI(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.setWindowTitle("UPLOWER - User Portal")
        self.resize(1450, 840)
        self.setMinimumSize(1100, 720)
        self.current_btn = None

        self.setStyleSheet(f"""
        QWidget {{
            background:{BG};
            color:{TEXT};
            font-family:Segoe UI, Arial;
            font-size:15px;
        }}
        QLabel {{ border:none; background:transparent; }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self.create_sidebar()
        self.stack = QStackedWidget()

        pages = [
            UploadUI(),
            MyUploadsUI(),
            ProfileUI(role="user", current_user=self.current_user),
        ]
        for page in pages:
            self.stack.addWidget(page)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack)
        self.set_active(self.btn_upload, 0)

    def create_sidebar(self):
        side = QFrame()
        side.setFixedWidth(320)
        side.setStyleSheet(f"""
        QFrame {{ background:{SIDEBAR}; border-right:1px solid {BORDER}; }}
        """)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        logo_row = QHBoxLayout()
        logo = QLabel("☁")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(52, 52)
        logo.setStyleSheet(f"""
        background:{GRADIENT}; border-radius:18px; font-size:25px; font-weight:bold;
        """)
        text_box = QVBoxLayout()
        title = QLabel("UPLOWER")
        title.setStyleSheet("font-size:25px; font-weight:900; color:#e879f9;")
        sub = QLabel("User Portal")
        sub.setStyleSheet(f"color:{TEXT2}; font-size:14px;")
        text_box.addWidget(title)
        text_box.addWidget(sub)
        logo_row.addWidget(logo)
        logo_row.addLayout(text_box)
        logo_row.addStretch()
        layout.addLayout(logo_row)
        layout.addSpacing(25)

        self.btn_upload = self.nav_button("⇧", "Upload Files")
        self.btn_myuploads = self.nav_button("▤", "My Uploads")
        self.btn_profile = self.nav_button("♡", "Hồ Sơ")

        buttons = [
            (self.btn_upload, 0),
            (self.btn_myuploads, 1),
            (self.btn_profile, 2),
        ]
        for btn, index in buttons:
            btn.clicked.connect(lambda checked, b=btn, i=index: self.set_active(b, i))
            layout.addWidget(btn)

        layout.addStretch()
        logout = self.nav_button("↪", "Logout")
        logout.clicked.connect(self.logout)
        layout.addWidget(logout)
        return side

    def nav_button(self, icon, text):
        btn = QPushButton(f"{icon}   {text}")
        btn.setFixedHeight(62)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self.nav_normal_style())
        return btn

    def nav_normal_style(self):
        return f"""
        QPushButton {{
            background:transparent; color:{TEXT2}; border:none; border-radius:14px;
            text-align:left; padding-left:22px; font-size:18px; font-weight:bold;
        }}
        QPushButton:hover {{ background:#1f1238; color:white; }}
        """

    def nav_active_style(self):
        return f"""
        QPushButton {{
            background:#30174f; color:#d18cff; border:1px solid {PRIMARY}; border-radius:14px;
            text-align:left; padding-left:22px; font-size:18px; font-weight:bold;
        }}
        """

    def set_active(self, btn, index):
        if self.current_btn:
            self.current_btn.setStyleSheet(self.nav_normal_style())
        btn.setStyleSheet(self.nav_active_style())
        self.current_btn = btn
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if hasattr(page, "refresh_history"):
            page.refresh_history()
        if hasattr(page, "refresh_stats"):
            page.refresh_stats()

    def page_base(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(28)
        scroll.setWidget(content)
        return scroll, layout

    def topbar(self, title, subtitle):
        row = QHBoxLayout()
        left = QVBoxLayout()
        h = QLabel(title)
        h.setStyleSheet("font-size:36px; font-weight:900; border:none;")
        p = QLabel(subtitle)
        p.setStyleSheet("font-size:20px; color:#b5c7e8; border:none;")
        left.addWidget(h)
        left.addWidget(p)
        search = QLineEdit()
        search.setPlaceholderText("⌕  Search...")
        search.setFixedSize(320, 52)
        search.setStyleSheet(self.input_style())
        bell = QPushButton("♧")
        bell.setFixedSize(54, 54)
        bell.setStyleSheet(self.icon_btn())
        user = QPushButton("♙")
        user.setFixedSize(62, 62)
        user.setStyleSheet(f"""
        QPushButton {{ background:{GRADIENT}; border:none; border-radius:20px; font-size:28px; font-weight:bold; }}
        """)
        row.addLayout(left)
        row.addStretch()
        row.addWidget(search)
        row.addWidget(bell)
        row.addWidget(user)
        return row

    def dashboard(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Dashboard", "Theo dõi hoạt động upload file của bạn"))
        grid = QHBoxLayout(); grid.setSpacing(30)
        grid.addWidget(self.stat_card("⇧", "0", "Total Uploads", "+0%"))
        grid.addWidget(self.stat_card("✓", "0%", "Success Rate", "+0%"))
        grid.addWidget(self.stat_card("▤", "0 MB", "Storage Used", "+0 MB"))
        grid.addWidget(self.stat_card("□", "0", "Active Files", "+0%"))
        layout.addLayout(grid)
        body = QHBoxLayout(); body.setSpacing(30)
        body.addWidget(self.empty_card("Upload Activity", "Chưa có dữ liệu upload"), 1)
        body.addWidget(self.storage_card(), 1)
        layout.addLayout(body)
        layout.addStretch()
        return page

    def my_files(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("My Files", "Manage and organize your uploaded files"))
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Uploaded", "Status", "Actions"])
        table.setRowCount(0)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMinimumHeight(360)
        table.setStyleSheet(self.table_style())
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        empty = QLabel("Chưa có file nào được upload")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet("color:#94a3b8; font-size:18px; padding:40px; border:none; background:transparent;")
        layout.addWidget(empty)
        return page

    def statistics(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Statistics", "View your upload and storage statistics"))
        grid = QHBoxLayout(); grid.setSpacing(30)
        grid.addWidget(self.stat_card("⇧", "0", "Total Uploads", "+0%"))
        grid.addWidget(self.stat_card("⇩", "0", "Total Downloads", "+0%"))
        grid.addWidget(self.stat_card("▰", "0 MB", "Storage Used", "+0 MB"))
        grid.addWidget(self.stat_card("⌁", "0 MB/s", "Avg Upload Speed", "+0 MB/s"))
        layout.addLayout(grid)
        body = QHBoxLayout(); body.setSpacing(30)
        body.addWidget(self.empty_card("Upload Trend (30 Days)", "Chưa có dữ liệu thống kê"), 1)
        body.addWidget(self.empty_card("File Type Distribution", "Chưa có dữ liệu phân loại file"), 1)
        layout.addLayout(body)
        return page

    def simple_page(self, title, subtitle):
        page, layout = self.page_base()
        layout.addLayout(self.topbar(title, subtitle))
        layout.addWidget(self.empty_card(title, "Nội dung sẽ bổ sung sau"))
        layout.addStretch()
        return page

    def stat_card(self, icon, value, label, change):
        card = QFrame(); card.setFixedHeight(210); card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card); box.setContentsMargins(30, 26, 30, 24); box.setSpacing(10)
        top = QHBoxLayout()
        icon_box = QLabel(icon); icon_box.setAlignment(Qt.AlignCenter); icon_box.setFixedSize(60, 60)
        icon_box.setStyleSheet("background:#321750; color:#c084fc; border-radius:16px; font-size:30px; border:none;")
        ch = QLabel(change); ch.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ch.setStyleSheet(f"color:{GREEN if '-' not in change else RED}; font-size:16px; font-weight:bold; border:none; background:transparent;")
        top.addWidget(icon_box); top.addStretch(); top.addWidget(ch)
        num = QLabel(value); num.setStyleSheet("font-size:32px; font-weight:900; color:white; border:none; background:transparent;")
        name = QLabel(label); name.setStyleSheet("font-size:17px; color:#b5c7e8; border:none; background:transparent;")
        box.addLayout(top); box.addStretch(); box.addWidget(num); box.addWidget(name)
        return card

    def storage_card(self):
        card = QFrame(); card.setMinimumHeight(410); card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card); box.setContentsMargins(30, 28, 30, 28)
        title = QLabel("Storage Usage"); title.setStyleSheet("font-size:24px; font-weight:900; border:none; background:transparent;")
        circle = QLabel("0%\nUsed"); circle.setAlignment(Qt.AlignCenter); circle.setFixedSize(190, 190)
        circle.setStyleSheet("QLabel { border:14px solid #334155; border-radius:95px; font-size:24px; font-weight:800; color:white; background:transparent; }")
        desc = QLabel("0 MB of 0 MB used"); desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size:16px; color:#b5c7e8; border:none; background:transparent;")
        box.addWidget(title); box.addStretch(); box.addWidget(circle, alignment=Qt.AlignCenter); box.addWidget(desc); box.addStretch()
        return card

    def empty_card(self, title, message):
        card = QFrame(); card.setMinimumHeight(410); card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card); box.setContentsMargins(30, 28, 30, 28)
        t = QLabel(title); t.setStyleSheet("font-size:24px; font-weight:900; border:none; background:transparent;")
        msg = QLabel(message); msg.setAlignment(Qt.AlignCenter); msg.setStyleSheet("color:#94a3b8; font-size:18px; border:none; background:transparent;")
        box.addWidget(t); box.addStretch(); box.addWidget(msg); box.addStretch()
        return card

    def card_style(self):
        return f"QFrame {{ background:{CARD}; border:1px solid {BORDER}; border-radius:18px; }}"

    def input_style(self):
        return f"QLineEdit {{ background:{CARD}; color:{TEXT}; border:1px solid #334155; border-radius:14px; padding-left:16px; font-size:18px; }}"

    def icon_btn(self):
        return f"""
        QPushButton {{ background:{CARD}; color:white; border:1px solid #334155; border-radius:14px; font-size:25px; }}
        QPushButton:hover {{ border:1px solid {PRIMARY}; }}
        """

    def table_style(self):
        return f"""
        QTableWidget {{ background:{CARD}; border:1px solid {BORDER}; border-radius:18px; color:white; font-size:17px; }}
        QHeaderView::section {{ background:#13162a; color:#b5c7e8; border:none; padding:14px; font-size:18px; font-weight:bold; }}
        QTableWidget::item {{ border-bottom:1px solid #1f2937; padding:12px; }}
        """

    def logout(self):
        from auth.login_ui import LoginUI
        self.login_window = LoginUI(initial_role="user")
        self.login_window.show()
        self.close()
