import json
import os

from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt

from client.upload_history import load_upload_history
from layout.theme import *


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE_FILE = os.path.join(BASE_DIR, "config", "profile_data.json")


class ProfileUI(QWidget):
    def __init__(self, role="user", current_user=None):
        super().__init__()
        self.role = role
        self.current_user = current_user or {}
        self.inputs = {}
        self.about_edit = None

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
        """)

        self.profile = self.load_profile()
        self.build_ui()
        self.refresh_stats()

    def default_profile(self):
        user_name = self.current_user.get("full_name")
        user_email = self.current_user.get("email")
        if self.role == "admin":
            return {
                "name": user_name or "Quản trị viên",
                "email": user_email or "admin@uplower.local",
                "phone": "",
                "address": "",
                "department": "Hệ thống",
                "position": "Admin",
                "about": "Quản lý máy chủ nhận tệp và theo dõi các phiên upload.",
            }
        return {
            "name": user_name or "User Demo",
            "email": user_email or "user@uplower.local",
            "phone": "",
            "address": "",
            "department": "Client",
                "position": "User",
                "about": "Tài khoản dùng để gửi file lên máy chủ.",
            }

    def load_profile(self):
        data = {}
        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    data = loaded if isinstance(loaded, dict) else {}
        except Exception:
            data = {}

        profile = self.default_profile()
        profile.update(data.get(self.role, {}))
        return profile

    def save_profile_data(self):
        all_profiles = {}
        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    all_profiles = loaded if isinstance(loaded, dict) else {}
        except Exception:
            all_profiles = {}

        data = {key: field.text().strip() for key, field in self.inputs.items()}
        data["about"] = self.about_edit.toPlainText().strip() if self.about_edit else ""
        all_profiles[self.role] = data

        os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_profiles, f, indent=2, ensure_ascii=False)
        self.profile.update(data)
        self.update_identity()
        QMessageBox.information(self, "UPLOWER", "Đã lưu thông tin hồ sơ.")

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 35, 40, 35)
        root.setSpacing(26)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Hồ sơ của tôi" if self.role == "user" else "Hồ sơ Admin")
        title.setStyleSheet("font-size:36px; font-weight:900;")
        sub = QLabel("Cập nhật thông tin tài khoản và xem thống kê liên quan")
        sub.setStyleSheet(f"font-size:20px; color:{TEXT2};")
        title_box.addWidget(title)
        title_box.addWidget(sub)

        save_btn = QPushButton("Lưu hồ sơ")
        save_btn.setFixedSize(150, 52)
        save_btn.setStyleSheet(self.primary_button_style())
        save_btn.clicked.connect(self.save_profile_data)

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(save_btn)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(26)
        body.addWidget(self.identity_card(), 1)
        body.addWidget(self.form_card(), 2)
        root.addLayout(body)

        bottom = QHBoxLayout()
        bottom.setSpacing(26)
        bottom.addWidget(self.stats_card(), 1)
        bottom.addWidget(self.about_card(), 2)
        root.addLayout(bottom)
        root.addStretch()

    def identity_card(self):
        card = QFrame()
        card.setMinimumHeight(330)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setAlignment(Qt.AlignCenter)
        box.setSpacing(14)

        avatar = QLabel("AD" if self.role == "admin" else "US")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(150, 150)
        avatar.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            color:white;
            border-radius:75px;
            font-size:42px;
            font-weight:900;
        }}
        """)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size:25px; font-weight:900;")
        self.role_label = QLabel()
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.setStyleSheet(f"font-size:17px; color:{TEXT2};")
        self.department_label = QLabel()
        self.department_label.setAlignment(Qt.AlignCenter)
        self.department_label.setStyleSheet(f"font-size:15px; color:{TEXT2};")

        box.addWidget(avatar)
        box.addWidget(self.name_label)
        box.addWidget(self.role_label)
        box.addWidget(self.department_label)
        self.update_identity()
        return card

    def form_card(self):
        card = QFrame()
        card.setMinimumHeight(330)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(18)

        title = QLabel("Thông tin cá nhân")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)

        fields = [
            ("name", "Họ và tên"),
            ("email", "Email"),
            ("phone", "Số điện thoại"),
            ("address", "Địa chỉ"),
            ("position", "Chức vụ"),
            ("department", "Phòng ban"),
        ]

        for index, (key, label_text) in enumerate(fields):
            label = QLabel(label_text)
            label.setStyleSheet(f"font-size:15px; color:{TEXT2}; font-weight:bold;")
            edit = QLineEdit(self.profile.get(key, ""))
            edit.setFixedHeight(48)
            edit.setStyleSheet(self.input_style())
            self.inputs[key] = edit
            row = index // 2 * 2
            col = index % 2
            grid.addWidget(label, row, col)
            grid.addWidget(edit, row + 1, col)

        box.addLayout(grid)
        return card

    def stats_card(self):
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(14)

        title = QLabel("Thống kê tài khoản")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        box.addWidget(title)

        self.stat_uploads = self.stat_row("Tổng lượt upload", "0")
        self.stat_success = self.stat_row("Verified", "0")
        self.stat_skipped = self.stat_row("Skipped", "0")
        self.stat_storage = self.stat_row("Dung lượng đã upload", "0 MB")
        for row in (self.stat_uploads, self.stat_success, self.stat_skipped, self.stat_storage):
            box.addWidget(row)
        return card

    def about_card(self):
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(30, 28, 30, 28)
        box.setSpacing(14)

        title = QLabel("Giới thiệu")
        title.setStyleSheet("font-size:24px; font-weight:900;")
        self.about_edit = QTextEdit()
        self.about_edit.setText(self.profile.get("about", ""))
        self.about_edit.setStyleSheet(f"""
        QTextEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding:14px;
            font-size:16px;
        }}
        """)
        box.addWidget(title)
        box.addWidget(self.about_edit)
        return card

    def stat_row(self, name, value):
        row = QFrame()
        row.setFixedHeight(48)
        row.setStyleSheet("background:#13162a; border:none; border-radius:12px;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 0, 16, 0)
        label = QLabel(name)
        label.setStyleSheet(f"font-size:15px; color:{TEXT2};")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:16px; font-weight:900; color:white;")
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(value_label)
        row.value_label = value_label
        return row

    def refresh_stats(self):
        user_email = None
        if self.role == "user":
            user_email = self.current_user.get("email", "")
        records = load_upload_history(user_email)
        verified = [r for r in records if r.get("status") == "Verified"]
        skipped = [r for r in records if r.get("status") == "Skipped"]
        total_size = sum(int(r.get("file_size", 0) or 0) for r in verified)
        self.stat_uploads.value_label.setText(str(len(records)))
        self.stat_success.value_label.setText(str(len(verified)))
        self.stat_skipped.value_label.setText(str(len(skipped)))
        self.stat_storage.value_label.setText(self.format_bytes(total_size))

    def update_identity(self):
        if hasattr(self, "name_label"):
            self.name_label.setText(self.profile.get("name", ""))
            self.role_label.setText(self.profile.get("position", self.role.title()))
            self.department_label.setText(self.profile.get("department", ""))

    def card_style(self):
        return f"QFrame {{ background:{CARD}; border:1px solid {BORDER}; border-radius:18px; }}"

    def input_style(self):
        return f"""
        QLineEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:14px;
            font-size:16px;
        }}
        QLineEdit:focus {{ border:1px solid {PRIMARY}; }}
        """

    def primary_button_style(self):
        return f"""
        QPushButton {{
            background:{GRADIENT};
            color:white;
            border:none;
            border-radius:14px;
            font-size:16px;
            font-weight:900;
        }}
        QPushButton:hover {{ background:#ec4899; }}
        """

    def format_bytes(self, value):
        value = float(value or 0)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024
