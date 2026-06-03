from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from layout.theme import *
from server.server_monitor_ui import ServerMonitorUI


class AdminUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPLOWER - Admin Panel")
        self.resize(1450, 850)
        self.setMinimumSize(1100, 720)
        self.current_btn = None

        self.setStyleSheet(f"""
        QWidget {{
            background:{BG};
            color:{TEXT};
            font-family:Segoe UI, Arial;
            font-size:15px;
        }}

        QLabel {{
            border:none;
            background:transparent;
        }}

        QPushButton {{
            border:none;
        }}

        QLineEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:16px;
        }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self.create_sidebar()
        self.stack = QStackedWidget()

        pages = [
            self.dashboard(),
            self.users_page_ui(),
            self.files_page_ui(),
            self.analytics_page_ui(),
            self.security_page_ui(),
            ServerMonitorUI(),
            self.simple_page("Hồ Sơ", "Thông tin tài khoản Admin"),
            self.simple_page("Settings", "Cài đặt hệ thống"),
        ]

        for page in pages:
            self.stack.addWidget(page)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack)

        self.set_active(self.btn_dashboard, 0)

    def create_sidebar(self):
        side = QFrame()
        side.setFixedWidth(320)
        side.setStyleSheet(f"""
        QFrame {{
            background:{SIDEBAR};
            border-right:1px solid {BORDER};
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)

        layout = QVBoxLayout(side)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(14)

        logo_row = QHBoxLayout()

        logo = QLabel("☁")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(52, 52)
        logo.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            border-radius:18px;
            font-size:26px;
            font-weight:bold;
            border:none;
        }}
        """)

        name_box = QVBoxLayout()
        title = QLabel("UPLOWER")
        title.setStyleSheet("font-size:25px; font-weight:900; color:#e879f9; border:none; background:transparent;")

        sub = QLabel("Admin Panel")
        sub.setStyleSheet(f"color:{TEXT2}; font-size:14px; border:none; background:transparent;")

        name_box.addWidget(title)
        name_box.addWidget(sub)

        logo_row.addWidget(logo)
        logo_row.addLayout(name_box)
        logo_row.addStretch()

        layout.addLayout(logo_row)
        layout.addSpacing(28)

        self.btn_dashboard = self.nav_button("⌂", "Dashboard")
        self.btn_users = self.nav_button("♧", "Users")
        self.btn_files = self.nav_button("▤", "Files")
        self.btn_analytics = self.nav_button("▥", "Analytics")
        self.btn_security = self.nav_button("♢", "Security")
        self.btn_server = self.nav_button("▣", "Server")
        self.btn_profile = self.nav_button("♡", "Hồ Sơ")
        self.btn_settings = self.nav_button("⚙", "Settings")

        buttons = [
            (self.btn_dashboard, 0),
            (self.btn_users, 1),
            (self.btn_files, 2),
            (self.btn_analytics, 3),
            (self.btn_security, 4),
            (self.btn_server, 5),
            (self.btn_profile, 6),
            (self.btn_settings, 7),
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
        btn.setFixedHeight(60)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self.nav_normal_style())
        return btn

    def nav_normal_style(self):
        return f"""
        QPushButton {{
            background:transparent;
            color:{TEXT2};
            border:none;
            border-radius:14px;
            text-align:left;
            padding-left:22px;
            font-size:18px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#171b2d;
            color:white;
        }}
        """

    def nav_active_style(self):
        return f"""
        QPushButton {{
            background:#30174f;
            color:#d18cff;
            border:1px solid {PRIMARY};
            border-radius:14px;
            text-align:left;
            padding-left:22px;
            font-size:18px;
            font-weight:bold;
        }}
        """

    def set_active(self, btn, index):
        if self.current_btn:
            self.current_btn.setStyleSheet(self.nav_normal_style())

        btn.setStyleSheet(self.nav_active_style())
        self.current_btn = btn
        self.stack.setCurrentIndex(index)

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

    def topbar(self, title, subtitle, add_btn=False):
        row = QHBoxLayout()

        left = QVBoxLayout()

        h = QLabel(title)
        h.setStyleSheet("font-size:36px; font-weight:900; border:none; background:transparent;")

        p = QLabel(subtitle)
        p.setStyleSheet("font-size:20px; color:#b5c7e8; border:none; background:transparent;")

        left.addWidget(h)
        left.addWidget(p)

        search = QLineEdit()
        search.setPlaceholderText("⌕  Search...")
        search.setFixedSize(320, 52)
        search.setStyleSheet(self.input_style())

        bell = QPushButton("♧")
        bell.setFixedSize(54, 54)
        bell.setStyleSheet(self.icon_button())

        shield = QPushButton("♢")
        shield.setFixedSize(62, 62)
        shield.setStyleSheet(f"""
        QPushButton {{
            background:{GRADIENT};
            border-radius:20px;
            font-size:28px;
            font-weight:bold;
            border:none;
        }}
        """)

        row.addLayout(left)
        row.addStretch()
        row.addWidget(search)
        row.addWidget(bell)
        row.addWidget(shield)

        if add_btn:
            add = QPushButton("♙  Add User")
            add.setFixedSize(150, 52)
            add.setStyleSheet(self.primary_button_style())
            row.addWidget(add)

        return row

    def dashboard(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Admin Dashboard", "Monitor and manage system activities"))

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("♧", "0", "Total Users", "+0%"))
        stats.addWidget(self.stat_card("▤", "0", "Total Files", "+0%"))
        stats.addWidget(self.stat_card("▭", "0%", "Server Load", "+0%"))
        stats.addWidget(self.stat_card("▰", "0 MB", "Storage", "+0 MB"))
        layout.addLayout(stats)

        health = QFrame()
        health.setMinimumHeight(170)
        health.setStyleSheet(self.card_style())

        hbox = QVBoxLayout(health)
        hbox.setContentsMargins(30, 28, 30, 28)

        title = QLabel("System Health")
        title.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        hbox.addWidget(title)

        row = QHBoxLayout()

        for name, value in [
            ("CPU Usage", 0),
            ("Memory", 0),
            ("Disk Space", 0),
            ("Network", 0),
        ]:
            col = QVBoxLayout()

            lab = QLabel(f"{name}                 {value}%")
            lab.setStyleSheet("font-size:16px; color:#b5c7e8; border:none; background:transparent;")

            bar = QProgressBar()
            bar.setValue(value)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet(self.progress_style())

            col.addWidget(lab)
            col.addWidget(bar)
            row.addLayout(col)

        hbox.addLayout(row)
        layout.addWidget(health)

        bottom = QHBoxLayout()
        bottom.setSpacing(30)
        bottom.addWidget(self.list_card("Recent Users", []))
        bottom.addWidget(self.list_card("Pending Approvals", []))
        layout.addLayout(bottom)

        layout.addWidget(self.bar_chart_card("Upload Activity (Last 30 Days)"))
        return page

    def users_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Users Management", "Manage and monitor all system users", add_btn=True))

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("♙", "0", "Total Users"))
        stats.addWidget(self.stat_card("♢", "0", "Active Users"))
        stats.addWidget(self.stat_card("✉", "0", "Pending"))
        stats.addWidget(self.stat_card("⊘", "0", "Inactive"))
        layout.addLayout(stats)

        layout.addWidget(self.empty_table(["User", "Role", "Files", "Storage", "Joined", "Status"], 430))
        return page

    def files_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Files Management", "Monitor and manage all uploaded files"))

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("▤", "0", "Total Files"))
        stats.addWidget(self.stat_card("✓", "0", "Approved"))
        stats.addWidget(self.stat_card("◷", "0", "Pending"))
        stats.addWidget(self.stat_card("⊗", "0", "Rejected"))
        layout.addLayout(stats)

        layout.addWidget(self.empty_table(["File Name", "User", "Type", "Size", "Uploaded", "Status", "Actions"], 520))
        return page

    def analytics_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Analytics", "Detailed analytics and insights"))

        layout.addWidget(self.bar_chart_card("System Activity (30 Days)"))

        bottom = QHBoxLayout()
        bottom.setSpacing(30)
        bottom.addWidget(self.small_info_card("User Growth", "No data", "0", "+0%"))
        bottom.addWidget(self.small_info_card("Upload Statistics", "No files", "0", "files"))
        bottom.addWidget(self.small_info_card("Storage Distribution", "Used", "0 MB", "0%"))
        layout.addLayout(bottom)

        return page

    def security_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Security", "Monitor and manage system security"))

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("⊙", "0", "Active Sessions"))
        stats.addWidget(self.stat_card("▣", "0", "Failed Logins"))
        stats.addWidget(self.stat_card("⚠", "0", "Security Alerts"))
        stats.addWidget(self.stat_card("♢", "0", "Blocked IPs"))
        layout.addLayout(stats)

        body = QHBoxLayout()
        body.setSpacing(30)

        settings = QFrame()
        settings.setMinimumHeight(380)
        settings.setStyleSheet(self.card_style())

        box = QVBoxLayout(settings)
        box.setContentsMargins(30, 28, 30, 28)

        t = QLabel("Security Settings")
        t.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        box.addWidget(t)

        for text, checked in [
            ("Two-Factor Authentication", False),
            ("IP Whitelist", False),
            ("Auto-lock Sessions", False),
            ("Audit Logging", False),
        ]:
            row = QFrame()
            row.setFixedHeight(60)
            row.setStyleSheet("QFrame { background:#13162a; border:none; border-radius:14px; } QLabel { border:none; background:transparent; }")

            r = QHBoxLayout(row)

            lab = QLabel(text)
            lab.setStyleSheet("font-size:17px; font-weight:bold; border:none; background:transparent;")

            cb = QCheckBox()
            cb.setChecked(checked)

            r.addWidget(lab)
            r.addStretch()
            r.addWidget(cb)

            box.addWidget(row)

        policy = QFrame()
        policy.setMinimumHeight(380)
        policy.setStyleSheet(self.card_style())

        pbox = QVBoxLayout(policy)
        pbox.setContentsMargins(30, 28, 30, 28)

        pt = QLabel("Password Policy")
        pt.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        pbox.addWidget(pt)

        length = QLineEdit()
        length.setPlaceholderText("Minimum Length")

        expiry = QLineEdit()
        expiry.setPlaceholderText("Password Expiry (days)")

        for label, inp in [
            ("Minimum Length", length),
            ("Password Expiry (days)", expiry),
        ]:
            lb = QLabel(label)
            lb.setStyleSheet("font-size:16px; color:#b5c7e8; border:none; background:transparent;")

            inp.setFixedHeight(52)
            inp.setStyleSheet(self.input_style())

            pbox.addWidget(lb)
            pbox.addWidget(inp)

        update = QPushButton("Update Policy")
        update.setFixedHeight(60)
        update.setStyleSheet(self.primary_button_style())
        pbox.addWidget(update)

        body.addWidget(settings)
        body.addWidget(policy)
        layout.addLayout(body)

        layout.addWidget(self.empty_table(["Event", "User", "IP Address", "Time", "Severity"], 360))
        return page

    def stat_card(self, icon, value, label, change=""):
        card = QFrame()
        card.setFixedHeight(210)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 26)

        top = QHBoxLayout()

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(60, 60)
        icon_box.setStyleSheet("""
        QLabel {
            background:#321750;
            color:#c084fc;
            border-radius:16px;
            font-size:30px;
            border:none;
        }
        """)

        ch = QLabel(change)
        ch.setAlignment(Qt.AlignRight)
        ch.setStyleSheet(
            f"color:{GREEN if '-' not in change else RED}; font-size:16px; font-weight:bold; border:none; background:transparent;"
        )

        top.addWidget(icon_box)
        top.addStretch()
        top.addWidget(ch)

        num = QLabel(value)
        num.setStyleSheet("font-size:30px; font-weight:900; border:none; background:transparent;")

        name = QLabel(label)
        name.setStyleSheet("font-size:17px; color:#b5c7e8; border:none; background:transparent;")

        box.addLayout(top)
        box.addStretch()
        box.addWidget(num)
        box.addWidget(name)

        return card

    def list_card(self, title, rows):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)

        t = QLabel(title)
        t.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        box.addWidget(t)

        empty = QLabel("Chưa có dữ liệu")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet("""
        color:#94a3b8;
        font-size:18px;
        padding:40px;
        border:none;
        background:transparent;
        """)
        box.addWidget(empty)
        box.addStretch()
        return card

    def empty_table(self, headers, height):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(0)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMinimumHeight(height)
        table.setStyleSheet(self.table_style())
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table

    def bar_chart_card(self, title):
        card = QFrame()
        card.setMinimumHeight(420)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)

        t = QLabel(title)
        t.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        box.addWidget(t)

        empty = QLabel("Chưa có dữ liệu thống kê")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet("color:#94a3b8;font-size:18px; border:none; background:transparent;")
        box.addWidget(empty)

        return card

    def small_info_card(self, title, label, value, extra):
        card = QFrame()
        card.setMinimumHeight(180)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)

        t = QLabel(title)
        t.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")

        l = QLabel(label)
        l.setStyleSheet("font-size:17px; color:#b5c7e8; border:none; background:transparent;")

        v = QLabel(f"{value}   {extra}")
        v.setStyleSheet("font-size:22px; font-weight:bold; border:none; background:transparent;")

        box.addWidget(t)
        box.addStretch()
        box.addWidget(l)
        box.addWidget(v)

        return card

    def simple_page(self, title, subtitle):
        page, layout = self.page_base()
        layout.addLayout(self.topbar(title, subtitle))

        card = QFrame()
        card.setMinimumHeight(400)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setAlignment(Qt.AlignCenter)

        label = QLabel("Nội dung sẽ bổ sung sau")
        label.setStyleSheet("font-size:24px; font-weight:bold; color:#b5c7e8; border:none; background:transparent;")
        box.addWidget(label)

        layout.addWidget(card)
        return page

    def card_style(self):
        return f"""
        QFrame {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}

        QLabel {{
            border:none;
            background:transparent;
        }}
        """

    def icon_button(self):
        return f"""
        QPushButton {{
            background:{CARD};
            color:white;
            border:1px solid #334155;
            border-radius:14px;
            font-size:25px;
        }}
        QPushButton:hover {{
            border:1px solid {PRIMARY};
        }}
        """

    def progress_style(self):
        return f"""
        QProgressBar {{
            background:#1e293b;
            border:none;
            border-radius:5px;
        }}
        QProgressBar::chunk {{
            background:{GREEN};
            border-radius:5px;
        }}
        """

    def input_style(self):
        return f"""
        QLineEdit {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:14px;
            padding-left:16px;
            font-size:17px;
        }}
        """

    def primary_button_style(self):
        return f"""
        QPushButton {{
            background:{GRADIENT};
            color:white;
            border:none;
            border-radius:14px;
            font-size:18px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#ec4899;
        }}
        """

    def table_style(self):
        return f"""
        QTableWidget {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
            color:white;
            font-size:17px;
            gridline-color:transparent;
        }}
        QHeaderView::section {{
            background:#13162a;
            color:#b5c7e8;
            border:none;
            padding:14px;
            font-size:18px;
            font-weight:bold;
        }}
        QTableWidget::item {{
            border:none;
            padding:12px;
        }}
        """

    def logout(self):
        from auth.login_ui import LoginUI
        self.login_window = LoginUI()
        self.login_window.show()
        self.close()