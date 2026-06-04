import json
import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from layout.theme import *
from auth.auth_manager import auth_manager
from client.upload_history import load_upload_history
from profile.profile_ui import ProfileUI
from server.server_monitor_ui import ServerMonitorUI

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "Uploads")
PROFILE_FILE = os.path.join(BASE_DIR, "config", "profile_data.json")

class AdminUI(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
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

        self.profile_page = ProfileUI(role="admin", current_user=self.current_user)
        self.profile_page.profile_saved.connect(self.refresh_account_badge)
        pages = [
            self.dashboard(),
            self.users_page_ui(),
            self.files_page_ui(),
            self.analytics_page_ui(),
            self.security_page_ui(),
            ServerMonitorUI(),
            self.profile_page,
            self.settings_page_ui(),
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
        layout.addWidget(self.account_badge())
        layout.addSpacing(16)

        self.btn_dashboard = self.nav_button("⌂", "Tổng quan")
        self.btn_users = self.nav_button("♧", "Tài khoản")
        self.btn_files = self.nav_button("▤", "File")
        self.btn_analytics = self.nav_button("▥", "Phân tích")
        self.btn_security = self.nav_button("♢", "Bảo mật")
        self.btn_server = self.nav_button("▣", "Server")
        self.btn_profile = self.nav_button("♡", "Hồ sơ")
        self.btn_settings = self.nav_button("⚙", "Cài đặt")

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

        logout = self.nav_button("↪", "Đăng xuất")
        logout.clicked.connect(self.logout)
        layout.addWidget(logout)

        return side

    def account_badge(self):
        badge = QFrame()
        badge.setFixedHeight(78)
        badge.setStyleSheet(f"""
        QFrame {{
            background:#13162a;
            border:1px solid {BORDER};
            border-radius:14px;
        }}
        QFrame:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)

        layout = QHBoxLayout(badge)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        self.sidebar_avatar = QLabel("AD")
        self.sidebar_avatar.setAlignment(Qt.AlignCenter)
        self.sidebar_avatar.setFixedSize(42, 42)
        self.sidebar_avatar.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            color:white;
            border-radius:14px;
            font-size:15px;
            font-weight:900;
        }}
        """)
        self.apply_sidebar_avatar(self.sidebar_avatar)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.sidebar_name = QLabel(self.current_user.get("full_name") or "Admin")
        self.sidebar_name.setStyleSheet("font-size:15px; font-weight:900; color:white;")
        self.sidebar_email = QLabel(self.current_user.get("email") or "admin@uplower.local")
        self.sidebar_email.setStyleSheet(f"font-size:12px; color:{TEXT2};")
        info.addWidget(self.sidebar_name)
        info.addWidget(self.sidebar_email)

        layout.addWidget(self.sidebar_avatar)
        layout.addLayout(info)
        return badge

    def refresh_account_badge(self):
        if hasattr(self, "profile_page"):
            self.sidebar_name.setText(self.profile_page.profile.get("name", "") or self.current_user.get("full_name") or "Admin")
        self.sidebar_email.setText(self.current_user.get("email") or "admin@uplower.local")
        self.apply_sidebar_avatar(self.sidebar_avatar)

    def profile_key(self):
        email = str(self.current_user.get("email", "")).strip().lower()
        return f"admin:{email}" if email else "admin"

    def current_avatar_path(self):
        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                profile = data.get(self.profile_key(), data.get("admin", {}))
                return profile.get("avatar_path", "") if isinstance(profile, dict) else ""
        except Exception:
            pass
        return ""

    def avatar_path_for_user(self, user):
        role = str(user.get("role", "user")).strip().lower() or "user"
        email = str(user.get("email", "")).strip().lower()
        profile_key = f"{role}:{email}" if email else role

        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                profile = data.get(profile_key, data.get(role, {}))
                return profile.get("avatar_path", "") if isinstance(profile, dict) else ""
        except Exception:
            pass
        return ""

    def avatar_label_for_user(self, user, size=96):
        role = str(user.get("role", "user")).strip().lower()
        fallback = "AD" if role == "admin" else "US"
        avatar = QLabel(fallback)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(size, size)

        avatar_path = self.avatar_path_for_user(user)
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                avatar.setText("")
                avatar.setPixmap(
                    pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                )
                avatar.setStyleSheet(f"""
                QLabel {{
                    background:#111827;
                    border:2px solid #475569;
                    border-radius:{size // 2}px;
                }}
                """)
                return avatar

        avatar.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            color:white;
            border-radius:{size // 2}px;
            font-size:30px;
            font-weight:900;
        }}
        """)
        return avatar

    def apply_sidebar_avatar(self, avatar_label):
        avatar_path = self.current_avatar_path()
        if not avatar_path or not os.path.exists(avatar_path):
            avatar_label.setPixmap(QPixmap())
            avatar_label.setText("AD")
            avatar_label.setStyleSheet(f"""
            QLabel {{
                background:{GRADIENT};
                color:white;
                border-radius:14px;
                font-size:15px;
                font-weight:900;
            }}
            """)
            return

        pixmap = QPixmap(avatar_path)
        if pixmap.isNull():
            avatar_label.setPixmap(QPixmap())
            avatar_label.setText("AD")
            return

        avatar_label.setText("")
        avatar_label.setPixmap(
            pixmap.scaled(42, 42, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        )
        avatar_label.setStyleSheet("""
        QLabel {
            background:#111827;
            border:1px solid #475569;
            border-radius:14px;
        }
        """)

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
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
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
        if index == 2:
            self.refresh_files_page()
        page = self.stack.currentWidget()
        if hasattr(page, "refresh_history"):
            page.refresh_history()
        if hasattr(page, "refresh_stats"):
            page.refresh_stats()

    def uploaded_files(self):
        files = []
        if not os.path.isdir(UPLOAD_DIR):
            return files
        for root, _dirs, names in os.walk(UPLOAD_DIR):
            for name in names:
                path = os.path.join(root, name)
                try:
                    stat = os.stat(path)
                except OSError:
                    continue
                rel_dir = os.path.relpath(root, UPLOAD_DIR)
                files.append({
                    "name": name,
                    "folder": "" if rel_dir == "." else rel_dir,
                    "size": stat.st_size,
                    "modified": self.format_timestamp(stat.st_mtime),
                    "path": path,
                    "type": os.path.splitext(name)[1].lower() or "file",
                })
        files.sort(key=lambda item: item["modified"], reverse=True)
        return files

    def upload_history(self):
        return load_upload_history()

    def admin_summary(self):
        users = auth_manager.list_users()
        files = self.uploaded_files()
        history = self.upload_history()
        verified = [item for item in history if item.get("status") == "Verified"]
        skipped = [item for item in history if item.get("status") == "Skipped"]
        failed = [item for item in history if item.get("status") in ("Failed", "Stopped")]
        return {
            "users": users,
            "files": files,
            "history": history,
            "verified": verified,
            "skipped": skipped,
            "failed": failed,
            "storage": sum(item["size"] for item in files),
        }

    def data_table(self, headers, rows, height=430):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMinimumHeight(height)
        table.setStyleSheet(self.table_style())
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for index in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)

        for row_index, row_values in enumerate(rows):
            for col_index, value in enumerate(row_values):
                table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        return table

    def format_bytes(self, value):
        value = float(value or 0)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024

    def format_timestamp(self, timestamp):
        try:
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "--"

    def display_account_status(self, status):
        return "Hoạt động" if status == "Active" else str(status or "--")

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
        search.setPlaceholderText("⌕  Tìm kiếm...")
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
            add = QPushButton("♙  Thêm user")
            add.setFixedSize(150, 52)
            add.setStyleSheet(self.primary_button_style())
            row.addWidget(add)

        return row

    def dashboard(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Tổng quan Admin", "Theo dõi user, phiên upload và dung lượng lưu trữ"))
        summary = self.admin_summary()
        users = summary["users"]
        files = summary["files"]
        history = summary["history"]

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("♙", str(len(users)), "Tổng user"))
        stats.addWidget(self.stat_card("▤", str(len(files)), "File đã lưu"))
        stats.addWidget(self.stat_card("✓", str(len(summary["verified"])), "Upload verified"))
        stats.addWidget(self.stat_card("▰", self.format_bytes(summary["storage"]), "Dung lượng"))
        layout.addLayout(stats)

        health = QFrame()
        health.setMinimumHeight(170)
        health.setStyleSheet(self.card_style())
        hbox = QVBoxLayout(health)
        hbox.setContentsMargins(30, 28, 30, 28)

        title = QLabel("Tình trạng hệ thống")
        title.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        hbox.addWidget(title)
        row = QHBoxLayout()

        for name, value in [
            ("Database xác thực", 100 if users else 0),
            ("Thư mục upload", 100 if os.path.isdir(UPLOAD_DIR) else 0),
            ("Dữ liệu lịch sử", 100 if history else 0),
            ("Phân quyền", 100),
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
        recent_users = [
            f"{user.get('full_name', '')} - {user.get('role', '')} - {user.get('status', '')}"
            for user in users[:5]
        ]
        recent_uploads = [
            f"{item.get('file_name', '')} - {item.get('status', '')} - {item.get('time', '')}"
            for item in history[:5]
        ]
        bottom.addWidget(self.list_card("User gần đây", recent_users))
        bottom.addWidget(self.list_card("Upload gần đây", recent_uploads))
        layout.addLayout(bottom)

        activity_rows = [
            [
                item.get("time", ""),
                item.get("file_name", ""),
                self.format_bytes(item.get("file_size", 0)),
                item.get("server", ""),
                item.get("status", ""),
            ]
            for item in history[:8]
        ]
        layout.addWidget(self.data_table(["Thời gian", "File", "Dung lượng", "Server", "Trạng thái"], activity_rows, 360))
        return page

    def users_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Quản lý tài khoản", "Quản lý tài khoản user và admin đã đăng ký"))

        users = auth_manager.list_users()
        total = len(users)
        active = sum(1 for user in users if user.get("status") == "Active")
        admins = sum(1 for user in users if user.get("role") == "admin")
        regular_users = sum(1 for user in users if user.get("role") == "user")

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("♙", str(total), "Tổng user"))
        stats.addWidget(self.stat_card("♢", str(active), "Đang hoạt động"))
        stats.addWidget(self.stat_card("▣", str(admins), "Admins"))
        stats.addWidget(self.stat_card("▤", str(regular_users), "Users"))
        layout.addLayout(stats)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["Họ tên", "Email", "Vai trò", "Ngày tạo", "Đăng nhập gần nhất", "Trạng thái", "Chi tiết"])
        table.setRowCount(len(users))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMinimumHeight(430)
        table.setStyleSheet(self.table_style())
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for index in range(1, 6):
            table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        table.setColumnWidth(6, 96)

        self.users = users
        self.users_table = table
        for row, user in enumerate(users):
            values = [
                user.get("full_name", ""),
                user.get("email", ""),
                user.get("role", ""),
                user.get("created_at", ""),
                user.get("last_login") or "--",
                self.display_account_status(user.get("status")),
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))

            detail_item = QTableWidgetItem("Xem")
            detail_item.setTextAlignment(Qt.AlignCenter)
            detail_item.setForeground(Qt.white)
            table.setItem(row, 6, detail_item)
            table.setRowHeight(row, 44)

        table.cellClicked.connect(
            lambda row, col: self.open_user_detail_dialog(self.users[row]) if col == 6 else None
        )
        table.cellDoubleClicked.connect(
            lambda row, col: self.open_user_detail_dialog(self.users[row]) if col != 6 else None
        )
        layout.addWidget(table)
        return page

    def detail_chip(self, label, value):
        chip = QFrame()
        chip.setObjectName("DetailChip")
        chip.setMinimumHeight(88)
        chip.setStyleSheet(f"""
        QFrame#DetailChip {{
            background:#13162a;
            border:1px solid #26324a;
            border-radius:14px;
        }}
        QFrame#DetailChip:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)
        box = QVBoxLayout(chip)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(6)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"font-size:14px; color:{TEXT2}; font-weight:bold;")
        value_widget = QLabel(str(value))
        value_widget.setStyleSheet("font-size:18px; color:white; font-weight:900;")
        value_widget.setWordWrap(True)
        chip.value_label = value_widget

        box.addWidget(label_widget)
        box.addWidget(value_widget)
        return chip

    def open_user_detail_dialog(self, user):
        email = str(user.get("email", "")).strip().lower()
        records = [
            record for record in self.upload_history()
            if str(record.get("user_email", "")).strip().lower() == email
        ]
        verified = [record for record in records if record.get("status") == "Verified"]
        skipped = [record for record in records if record.get("status") == "Skipped"]
        total_size = sum(int(record.get("file_size", 0) or 0) for record in verified)

        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết user")
        dialog.resize(980, 680)
        dialog.setStyleSheet(f"""
        QDialog {{
            background:{BG};
            color:{TEXT};
            font-family:Segoe UI, Arial;
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(18)
        header.addWidget(self.avatar_label_for_user(user, 96))

        title_box = QVBoxLayout()
        title_box.setSpacing(6)
        title = QLabel(user.get("full_name", "") or "Chi tiết user")
        title.setStyleSheet("font-size:30px; font-weight:900;")
        subtitle = QLabel(user.get("email", "") or "--")
        subtitle.setStyleSheet(f"font-size:17px; color:{TEXT2};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        account_grid = QHBoxLayout()
        account_grid.setSpacing(14)
        for chip in (
            self.detail_chip("Vai trò", user.get("role", "") or "--"),
            self.detail_chip("Trạng thái", self.display_account_status(user.get("status"))),
            self.detail_chip("Ngày tạo", user.get("created_at", "") or "--"),
            self.detail_chip("Đăng nhập gần nhất", user.get("last_login") or "--"),
        ):
            account_grid.addWidget(chip)
        layout.addLayout(account_grid)

        upload_grid = QHBoxLayout()
        upload_grid.setSpacing(14)
        for chip in (
            self.detail_chip("Tổng upload", str(len(records))),
            self.detail_chip("Verified", str(len(verified))),
            self.detail_chip("Skipped", str(len(skipped))),
            self.detail_chip("Dung lượng", self.format_bytes(total_size)),
        ):
            upload_grid.addWidget(chip)
        layout.addLayout(upload_grid)

        rows = [
            [
                record.get("time", ""),
                record.get("file_name", ""),
                self.format_bytes(record.get("file_size", 0)),
                record.get("server", ""),
                record.get("status", ""),
            ]
            for record in records[:5]
        ]

        recent_title = QLabel("Lịch sử upload gần đây")
        recent_title.setStyleSheet("font-size:22px; font-weight:900;")
        layout.addWidget(recent_title)
        layout.addWidget(self.data_table(["Thời gian", "File", "Dung lượng", "Server", "Trạng thái"], rows, 280))

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setFixedSize(120, 42)
        close_btn.setStyleSheet(self.primary_button_style())
        close_btn.clicked.connect(dialog.close)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        dialog.exec_()

    def files_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Quản lý file", "Quét và kiểm tra các file đang lưu trên Server"))

        stats = QHBoxLayout()
        stats.setSpacing(30)
        self.files_total_card = self.stat_card("▤", "0", "Tổng file")
        self.files_size_card = self.stat_card("▰", "0 B", "Tổng dung lượng")
        self.files_folders_card = self.stat_card("▣", "0", "Thư mục con")
        self.files_status_card = self.stat_card("✓", "Sẵn sàng", "Trạng thái lưu trữ")
        for card in (
            self.files_total_card,
            self.files_size_card,
            self.files_folders_card,
            self.files_status_card,
        ):
            stats.addWidget(card)
        layout.addLayout(stats)

        self.files_table = self.data_table(
            ["File", "Thư mục", "Người upload", "Loại", "Dung lượng", "Cập nhật", "Trạng thái", "Mở"],
            [],
            520,
        )
        self.files_table.cellClicked.connect(self.open_admin_file_from_table)
        self.files_table.horizontalHeader().setStretchLastSection(False)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for index in range(1, 7):
            self.files_table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.files_table.setColumnWidth(7, 72)
        layout.addWidget(self.files_table)
        self.refresh_files_page()
        return page

    def refresh_files_page(self):
        if not hasattr(self, "files_table"):
            return

        summary = self.admin_summary()
        files = summary["files"]
        history = summary["history"]
        folders = {item["folder"] for item in files if item["folder"]}
        uploader_by_file = {}

        for record in history:
            file_name = record.get("file_name", "")
            uploader = record.get("user_name") or record.get("user_email", "")
            if file_name and uploader and file_name not in uploader_by_file:
                uploader_by_file[file_name] = uploader

        self.files_total_card.value_label.setText(str(len(files)))
        self.files_size_card.value_label.setText(self.format_bytes(summary["storage"]))
        self.files_folders_card.value_label.setText(str(len(folders)))
        self.files_status_card.value_label.setText("Sẵn sàng")

        rows = [
            [
                item["name"],
                item["folder"] or "Uploads",
                uploader_by_file.get(item["name"], "--"),
                item["type"],
                self.format_bytes(item["size"]),
                item["modified"],
                "Đã lưu",
                "Mở",
            ]
            for item in files
        ]

        self.files_rows = files
        self.files_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col_index, value in enumerate(row_values):
                table_item = QTableWidgetItem(str(value))
                if col_index == 7:
                    table_item.setTextAlignment(Qt.AlignCenter)
                    table_item.setForeground(Qt.white)
                self.files_table.setItem(row_index, col_index, table_item)

    def open_admin_file_from_table(self, row, column):
        if column != 7:
            return
        files = getattr(self, "files_rows", [])
        if row < 0 or row >= len(files):
            return

        file_path = files[row].get("path", "")
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "UPLOWER", "Không tìm thấy file trên Server.")
            return

        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "UPLOWER", f"Không thể mở file: {e}")

    def analytics_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Phân tích", "Phân tích lịch sử upload và phân bố dung lượng lưu trữ"))
        summary = self.admin_summary()
        history = summary["history"]
        files = summary["files"]

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("✓", str(len(summary["verified"])), "Verified"))
        stats.addWidget(self.stat_card("↷", str(len(summary["skipped"])), "Skipped"))
        stats.addWidget(self.stat_card("✕", str(len(summary["failed"])), "Failed/Stopped"))
        stats.addWidget(self.stat_card("▰", self.format_bytes(summary["storage"]), "Dung lượng"))
        layout.addLayout(stats)

        by_status = {}
        for item in history:
            status = item.get("status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1
        status_rows = [[status, count] for status, count in sorted(by_status.items())]

        by_type = {}
        for item in files:
            file_type = item.get("type", "file")
            by_type[file_type] = by_type.get(file_type, 0) + 1
        type_rows = [[file_type, count] for file_type, count in sorted(by_type.items())]

        bottom = QHBoxLayout()
        bottom.setSpacing(30)
        bottom.addWidget(self.data_table(["Trạng thái", "Số lượng"], status_rows, 300))
        bottom.addWidget(self.data_table(["Loại file", "Số lượng"], type_rows, 300))
        layout.addLayout(bottom)

        recent_rows = [
            [
                item.get("time", ""),
                item.get("file_name", ""),
                self.format_bytes(item.get("file_size", 0)),
                item.get("speed", ""),
                item.get("status", ""),
            ]
            for item in history[:10]
        ]
        layout.addWidget(self.data_table(["Thời gian", "File", "Dung lượng", "Tốc độ", "Trạng thái"], recent_rows, 400))
        return page

    def security_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Bảo mật", "Kiểm tra xác thực, phân quyền và hoạt động tài khoản"))
        users = auth_manager.list_users()
        admins = [user for user in users if user.get("role") == "admin"]
        active = [user for user in users if user.get("status") == "Active"]
        logged_in = [user for user in users if user.get("last_login")]

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("✓", str(len(active)), "Tài khoản hoạt động"))
        stats.addWidget(self.stat_card("♙", str(len(admins)), "Tài khoản admin"))
        stats.addWidget(self.stat_card("◆", "Bật", "Hash mật khẩu"))
        stats.addWidget(self.stat_card("◇", "Bật", "Kiểm tra vai trò"))
        layout.addLayout(stats)

        policy_rows = [
            ["Lưu mật khẩu", "PBKDF2 SHA-256 với salt ngẫu nhiên", "Đã bật"],
            ["Admin mặc định", "admin@uplower.local", "Đã tạo"],
            ["Bảo vệ vai trò", "User không thể mở Admin Panel", "Đã bật"],
            ["Đăng ký", "Chỉ tạo tài khoản User", "Đã bật"],
            ["Database", auth_manager.db_path, "Sẵn sàng"],
        ]
        layout.addWidget(self.data_table(["Kiểm soát", "Chi tiết", "Trạng thái"], policy_rows, 300))

        activity_rows = [
            [
                user.get("full_name", ""),
                user.get("email", ""),
                user.get("role", ""),
                user.get("last_login") or "--",
                self.display_account_status(user.get("status")),
            ]
            for user in users
        ]
        layout.addWidget(self.data_table(["User", "Email", "Vai trò", "Đăng nhập gần nhất", "Trạng thái"], activity_rows, 360))
        return page

    def settings_page_ui(self):
        page, layout = self.page_base()
        layout.addLayout(self.topbar("Cài đặt", "Xem cấu hình runtime đang dùng bởi desktop app"))
        summary = self.admin_summary()

        stats = QHBoxLayout()
        stats.setSpacing(30)
        stats.addWidget(self.stat_card("▣", "SQLite", "Database xác thực"))
        stats.addWidget(self.stat_card("▤", str(len(summary["files"])), "File đã lưu"))
        stats.addWidget(self.stat_card("♧", str(len(summary["users"])), "Tài khoản"))
        stats.addWidget(self.stat_card("▰", self.format_bytes(summary["storage"]), "Dung lượng"))
        layout.addLayout(stats)

        rows = [
            ["Database", auth_manager.db_path],
            ["Thư mục upload", UPLOAD_DIR],
            ["Email admin mặc định", "admin@uplower.local"],
            ["Mật khẩu admin mặc định", "admin123"],
            ["Lịch sử client", "Code/config/client_upload_history.json"],
            ["Dữ liệu hồ sơ", "Code/config/profile_data.json"],
        ]
        layout.addWidget(self.data_table(["Cài đặt", "Giá trị"], rows, 420))
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

        card.value_label = num
        return card

    def list_card(self, title, rows):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())

        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(10)

        t = QLabel(title)
        t.setStyleSheet("font-size:23px; font-weight:900; border:none; background:transparent;")
        box.addWidget(t)

        if rows:
            for item in rows:
                row = QLabel(str(item))
                row.setMinimumHeight(34)
                row.setStyleSheet("""
                color:#dbeafe;
                font-size:15px;
                padding:6px 8px;
                border:none;
                background:#13162a;
                border-radius:8px;
                """)
                box.addWidget(row)
        else:
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

        QFrame:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
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
            background:#171832;
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        """

    def small_button_style(self):
        return f"""
        QPushButton {{
            background:{CARD2};
            color:white;
            border:1px solid #334155;
            border-radius:9px;
            font-size:14px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
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
        QPushButton:pressed {{
            background:#c026d3;
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
        QTableWidget::item:hover {{
            background:#1f1238;
            color:white;
        }}
        QTableWidget::item:selected {{
            background:#30174f;
            color:white;
        }}
        """

    def logout(self):
        from auth.login_ui import LoginUI
        self.login_window = LoginUI(initial_role="admin")
        self.login_window.show()
        self.close()
