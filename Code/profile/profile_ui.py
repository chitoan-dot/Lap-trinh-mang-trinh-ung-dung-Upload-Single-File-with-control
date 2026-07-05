import json
import os

from PyQt5.QtWidgets import (
    QFileDialog,
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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from client.upload_history import load_upload_history
from layout.theme import *


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE_FILE = os.path.join(BASE_DIR, "config", "profile_data.json")
PROFILE_AVATAR_SIZE = 120
PROFILE_AVATAR_RADIUS = PROFILE_AVATAR_SIZE // 2


class ProfileUI(QWidget):
    profile_saved = pyqtSignal()

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

    def profile_key(self):
        email = str(self.current_user.get("email", "")).strip().lower()
        return f"{self.role}:{email}" if email else self.role

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
                "avatar_path": "",
                "about": "Quản lý máy chủ nhận tệp và theo dõi các phiên upload.",
            }
        return {
            "name": user_name or "User Demo",
            "email": user_email or "user@uplower.local",
            "phone": "",
            "address": "",
            "department": "Client",
            "position": "User",
            "avatar_path": "",
            "about": "Tài khoản dùng để gửi file lên máy chủ.",
        }

    def read_profiles(self):
        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    return loaded if isinstance(loaded, dict) else {}
        except Exception:
            pass
        return {}

    def load_profile(self):
        data = self.read_profiles()
        profile = self.default_profile()
        profile.update(data.get(self.profile_key(), data.get(self.role, {})))
        return profile

    def save_profile_data(self):
        all_profiles = self.read_profiles()

        data = {key: field.text().strip() for key, field in self.inputs.items()}
        data["avatar_path"] = self.profile.get("avatar_path", "")
        data["about"] = self.about_edit.toPlainText().strip() if self.about_edit else ""
        all_profiles[self.profile_key()] = data

        os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_profiles, f, indent=2, ensure_ascii=False)
        self.profile.update(data)
        self.update_identity()
        self.profile_saved.emit()
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
        card.setObjectName("ProfileCard")
        card.setMinimumHeight(300)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(20, 18, 20, 18)
        box.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        box.setSpacing(10)

        self.avatar_label = QLabel("AD" if self.role == "admin" else "US")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setFixedSize(PROFILE_AVATAR_SIZE, PROFILE_AVATAR_SIZE)
        self.avatar_label.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            color:white;
            border-radius:{PROFILE_AVATAR_RADIUS}px;
            font-size:36px;
            font-weight:900;
        }}
        """)
        self.update_avatar_display()

        choose_avatar_btn = QPushButton("Chọn ảnh")
        choose_avatar_btn.setFixedSize(116, 34)
        choose_avatar_btn.setStyleSheet(self.secondary_button_style())
        choose_avatar_btn.clicked.connect(self.choose_avatar)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMinimumHeight(32)
        self.name_label.setStyleSheet("font-size:22px; font-weight:900;")
        self.role_label = QLabel()
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.setStyleSheet(f"font-size:15px; color:{TEXT2};")
        self.department_label = QLabel()
        self.department_label.setAlignment(Qt.AlignCenter)
        self.department_label.setStyleSheet(f"font-size:14px; color:{TEXT2};")

        box.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
        box.addWidget(choose_avatar_btn, alignment=Qt.AlignCenter)
        box.addWidget(self.name_label)
        box.addWidget(self.role_label)
        box.addWidget(self.department_label)
        self.update_identity()
        return card

    def form_card(self):
        card = QFrame()
        card.setObjectName("ProfileCard")
        card.setMinimumHeight(360)
        card.setStyleSheet(self.card_style())
        box = QVBoxLayout(card)
        box.setContentsMargins(28, 24, 28, 24)
        box.setSpacing(16)

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
            field = QWidget()
            field.setStyleSheet("background:transparent; border:none;")
            field_layout = QVBoxLayout(field)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)

            label = QLabel(label_text)
            label.setMinimumHeight(20)
            label.setStyleSheet(f"font-size:15px; color:{TEXT2}; font-weight:bold;")

            edit = QLineEdit(self.profile.get(key, ""))
            edit.setFixedHeight(46)
            edit.setStyleSheet(self.input_style())
            self.inputs[key] = edit

            field_layout.addWidget(label)
            field_layout.addWidget(edit)

            row = index // 2
            col = index % 2
            grid.addWidget(field, row, col)

        box.addLayout(grid)
        return card

    def choose_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh đại diện",
            "",
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not file_path:
            return

        self.profile["avatar_path"] = file_path
        self.update_avatar_display()

    def stats_card(self):
        card = QFrame()
        card.setObjectName("ProfileCard")
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
        card.setObjectName("ProfileCard")
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
            background:#111827;
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding:14px;
            font-size:16px;
        }}
        QTextEdit:hover {{
            background:#121c2d;
            border:1px solid #475569;
        }}
        QTextEdit:focus {{
            background:#121c2d;
            border:1px solid {PRIMARY};
        }}
        """)
        box.addWidget(title)
        box.addWidget(self.about_edit)
        return card

    def stat_row(self, name, value):
        row = QFrame()
        row.setObjectName("StatRow")
        row.setFixedHeight(48)
        row.setStyleSheet(f"""
        QFrame#StatRow {{
            background:#13162a;
            border:1px solid transparent;
            border-radius:12px;
        }}
        QFrame#StatRow:hover {{
            background:#171832;
            border:1px solid {BORDER};
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """)
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
            self.update_avatar_display()

    def update_avatar_display(self):
        if not hasattr(self, "avatar_label"):
            return

        avatar_path = self.profile.get("avatar_path", "")
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                self.avatar_label.setText("")
                self.avatar_label.setPixmap(
                    pixmap.scaled(
                        PROFILE_AVATAR_SIZE,
                        PROFILE_AVATAR_SIZE,
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation,
                    )
                )
                self.avatar_label.setStyleSheet(f"""
                QLabel {{
                    background:#111827;
                    border:2px solid #475569;
                    border-radius:{PROFILE_AVATAR_RADIUS}px;
                }}
                """)
                return

        self.avatar_label.setPixmap(QPixmap())
        self.avatar_label.setText("AD" if self.role == "admin" else "US")
        self.avatar_label.setStyleSheet(f"""
        QLabel {{
            background:{GRADIENT};
            color:white;
            border-radius:{PROFILE_AVATAR_RADIUS}px;
            font-size:36px;
            font-weight:900;
        }}
        """)

    def card_style(self):
        return f"""
        QFrame#ProfileCard {{
            background:#0f1024;
            border:1px solid #2d3752;
            border-radius:18px;
        }}
        QFrame#ProfileCard:hover {{
            background:#111427;
            border:1px solid #475569;
        }}
        QLabel {{
            border:none;
            background:transparent;
        }}
        """

    def input_style(self):
        return f"""
        QLineEdit {{
            background:#111827;
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:14px;
            font-size:16px;
        }}
        QLineEdit:hover {{
            background:#121c2d;
            border:1px solid #475569;
        }}
        QLineEdit:focus {{
            background:#121c2d;
            border:1px solid {PRIMARY};
        }}
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
        QPushButton:pressed {{ background:#c026d3; }}
        """

    def secondary_button_style(self):
        return f"""
        QPushButton {{
            background:#13162a;
            color:white;
            border:1px solid #334155;
            border-radius:11px;
            font-size:14px;
            font-weight:900;
        }}
        QPushButton:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        """

    def format_bytes(self, value):
        value = float(value or 0)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024
