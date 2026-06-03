import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QStackedWidget,
    QScrollArea
)
from PyQt5.QtCore import Qt

from layout.theme import *
from auth.auth_manager import auth_manager
from client.ui_client import ClientUI
from admin.ui_admin import AdminUI


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REMEMBER_LOGIN_FILE = os.path.join(BASE_DIR, "config", "remember_login.json")


class LoginUI(QWidget):
    def __init__(self, initial_role="user"):
        super().__init__()
        self.setWindowTitle("UPLOWER - Xác thực")
        self.resize(1100, 760)
        self.setMinimumSize(900, 760)

        self.role = initial_role if initial_role in ("user", "admin") else "user"
        self.app_window = None

        self.setStyleSheet(f"""
        QWidget {{
            background:{BG};
            color:{TEXT};
            font-family: Segoe UI, Arial;
        }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.login_page())
        self.stack.addWidget(self.register_page())

        root.addWidget(self.stack)
        self.set_role(self.role)
        self.load_remembered_login(self.role)

    def input_style(self):
        return f"""
        QLineEdit {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:14px;
            padding-left:14px;
            font-size:15px;
        }}
        QLineEdit:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QLineEdit:focus {{
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
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#ec4899;
        }}
        QPushButton:pressed {{
            background:#c026d3;
        }}
        """

    def link_button_style(self):
        return """
        QPushButton {
            background:transparent;
            border:none;
            color:#d66cff;
            font-size:15px;
            font-weight:bold;
        }
        QPushButton:hover {
            color:#ec4899;
        }
        QPushButton:pressed {
            color:#c026d3;
        }
        """

    def role_button_style(self, active=False):
        if active:
            return f"""
            QPushButton {{
                background:#30104d;
                color:white;
                border:1px solid {PRIMARY};
                border-radius:14px;
                font-weight:bold;
            }}
            QPushButton:hover {{
                background:#3b1760;
                border:1px solid #ec4899;
            }}
            QPushButton:pressed {{
                background:#4c1d95;
            }}
            """
        return f"""
        QPushButton {{
            background:{CARD2};
            color:{TEXT2};
            border:1px solid #334155;
            border-radius:14px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#171832;
            color:white;
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        """

    def make_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        card = QFrame()
        card.setFixedWidth(560)
        card.setStyleSheet("background:transparent; border:none;")

        box = QVBoxLayout(card)
        box.setSpacing(11)
        box.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(card)
        scroll.setWidget(content)

        return scroll, box

    def header(self, title_text, sub_text):
        logo = QLabel("☁")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(58, 58)
        logo.setStyleSheet(f"""
            background:{GRADIENT};
            color:white;
            border-radius:18px;
            font-size:26px;
            font-weight:bold;
        """)

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(48)
        title.setStyleSheet("""
            color:#d66cff;
            font-size:32px;
            font-weight:900;
        """)

        sub = QLabel(sub_text)
        sub.setAlignment(Qt.AlignCenter)
        sub.setMinimumHeight(25)
        sub.setStyleSheet(f"color:{TEXT2}; font-size:14px;")

        return logo, title, sub

    def label(self, text):
        lb = QLabel(text)
        lb.setMinimumHeight(22)
        lb.setStyleSheet("font-weight:bold; font-size:14px;")
        return lb

    def role_row(self, prefix):
        row = QHBoxLayout()
        row.setSpacing(15)

        user_btn = QPushButton("👤\nUser")
        admin_btn = QPushButton("🧑‍💼\nAdmin")

        user_btn.setFixedHeight(68)
        admin_btn.setFixedHeight(68)

        user_btn.clicked.connect(lambda: self.set_role("user"))
        admin_btn.clicked.connect(lambda: self.set_role("admin"))

        if prefix == "register":
            admin_btn.setEnabled(False)
            admin_btn.setToolTip("Admin mặc định do hệ thống cấp. Đăng ký mới chỉ tạo User.")

        setattr(self, f"{prefix}_user_btn", user_btn)
        setattr(self, f"{prefix}_admin_btn", admin_btn)

        row.addWidget(user_btn)
        row.addWidget(admin_btn)

        return row

    def login_page(self):
        page, box = self.make_page()
        logo, title, sub = self.header(
            "UPLOWER",
            "Hệ thống Upload Single File có điều khiển"
        )

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("✉  Nhập email hoặc tên đăng nhập")
        self.login_email.setFixedHeight(50)
        self.login_email.setStyleSheet(self.input_style())

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("🔒  Nhập mật khẩu")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setFixedHeight(50)
        self.login_password.setStyleSheet(self.input_style())
        self.login_password.returnPressed.connect(self.open_app)

        option_row = QHBoxLayout()
        self.remember_checkbox = QCheckBox("Ghi nhớ đăng nhập")
        self.remember_checkbox.setStyleSheet(f"""
        QCheckBox {{
            font-weight:bold;
            spacing:8px;
        }}
        QCheckBox::indicator {{
            width:16px;
            height:16px;
            border:1px solid #334155;
            border-radius:4px;
            background:{CARD2};
        }}
        QCheckBox::indicator:hover {{
            border:1px solid {PRIMARY};
            background:#171832;
        }}
        QCheckBox::indicator:checked {{
            background:{PRIMARY};
            border:1px solid {PRIMARY};
        }}
        """)

        forgot = QPushButton("Quên mật khẩu?")
        forgot.setStyleSheet(self.link_button_style())
        forgot.clicked.connect(
            lambda: QMessageBox.information(self, "UPLOWER", "Chức năng này sẽ bổ sung sau.")
        )

        option_row.addWidget(self.remember_checkbox)
        option_row.addStretch()
        option_row.addWidget(forgot)

        login_btn = QPushButton("Đăng nhập →")
        login_btn.setFixedHeight(50)
        login_btn.setStyleSheet(self.primary_button_style())
        login_btn.clicked.connect(self.open_app)

        google_btn = QPushButton("G  Đăng nhập với Google")
        google_btn.setFixedHeight(43)
        google_btn.setStyleSheet(f"""
        QPushButton {{
            background:{CARD2};
            color:{TEXT};
            border:1px solid #334155;
            border-radius:12px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:#171832;
            border:1px solid {PRIMARY};
        }}
        QPushButton:pressed {{
            background:#30174f;
        }}
        """)

        register_btn = QPushButton("Chưa có tài khoản? Đăng ký ngay")
        register_btn.setFixedHeight(42)
        register_btn.setStyleSheet(self.link_button_style())
        register_btn.clicked.connect(self.show_register)

        box.addWidget(logo, alignment=Qt.AlignCenter)
        box.addWidget(title)
        box.addWidget(sub)
        box.addSpacing(10)
        box.addLayout(self.role_row("login"))
        box.addWidget(self.label("Email hoặc tên đăng nhập"))
        box.addWidget(self.login_email)
        box.addWidget(self.label("Mật khẩu"))
        box.addWidget(self.login_password)
        box.addLayout(option_row)
        box.addWidget(login_btn)
        box.addWidget(google_btn)
        box.addWidget(register_btn)

        return page

    def register_page(self):
        page, box = self.make_page()
        logo, title, sub = self.header(
            "Đăng ký tài khoản",
            "Tạo tài khoản mới để sử dụng UPLOWER"
        )

        self.fullname = QLineEdit()
        self.fullname.setPlaceholderText("👤  Nhập họ và tên")
        self.fullname.setFixedHeight(44)
        self.fullname.setStyleSheet(self.input_style())

        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("✉  Nhập email")
        self.register_email.setFixedHeight(44)
        self.register_email.setStyleSheet(self.input_style())

        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("🔒  Nhập mật khẩu")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setFixedHeight(44)
        self.register_password.setStyleSheet(self.input_style())

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("🔒  Nhập lại mật khẩu")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setFixedHeight(44)
        self.confirm_password.setStyleSheet(self.input_style())

        self.agree = QCheckBox("Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật")
        self.agree.setMinimumHeight(28)
        self.agree.setStyleSheet(f"""
        QCheckBox {{
            font-weight:bold;
            spacing:8px;
        }}
        QCheckBox::indicator {{
            width:16px;
            height:16px;
            border:1px solid #334155;
            border-radius:4px;
            background:{CARD2};
        }}
        QCheckBox::indicator:hover {{
            border:1px solid {PRIMARY};
            background:#171832;
        }}
        QCheckBox::indicator:checked {{
            background:{PRIMARY};
            border:1px solid {PRIMARY};
        }}
        """)

        register_btn = QPushButton("Đăng ký")
        register_btn.setFixedHeight(46)
        register_btn.setStyleSheet(self.primary_button_style())
        register_btn.clicked.connect(self.register)

        login_btn = QPushButton("Đã có tài khoản? Đăng nhập ngay")
        login_btn.setFixedHeight(42)
        login_btn.setStyleSheet(self.link_button_style())
        login_btn.clicked.connect(self.show_login)

        box.addWidget(logo, alignment=Qt.AlignCenter)
        box.addWidget(title)
        box.addWidget(sub)
        box.addSpacing(4)
        box.addLayout(self.role_row("register"))
        box.addWidget(self.label("Họ và tên"))
        box.addWidget(self.fullname)
        box.addWidget(self.label("Email"))
        box.addWidget(self.register_email)
        box.addWidget(self.label("Mật khẩu"))
        box.addWidget(self.register_password)
        box.addWidget(self.label("Xác nhận mật khẩu"))
        box.addWidget(self.confirm_password)
        box.addWidget(self.agree)
        box.addWidget(register_btn)
        box.addWidget(login_btn)

        return page

    def set_role(self, role):
        self.role = role

        for prefix in ("login", "register"):
            user_btn = getattr(self, f"{prefix}_user_btn", None)
            admin_btn = getattr(self, f"{prefix}_admin_btn", None)

            if user_btn and admin_btn:
                user_btn.setStyleSheet(self.role_button_style(role == "user"))
                admin_btn.setStyleSheet(self.role_button_style(role == "admin"))

        if hasattr(self, "login_email") and hasattr(self, "remember_checkbox"):
            self.load_remembered_login(role)

    def show_register(self):
        self.set_role("user")
        self.stack.setCurrentIndex(1)
        self.setWindowTitle("UPLOWER - Đăng ký")

    def show_login(self):
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("UPLOWER - Đăng nhập")

    def read_remembered_logins(self):
        try:
            if not os.path.exists(REMEMBER_LOGIN_FILE):
                return {"accounts": {}}

            with open(REMEMBER_LOGIN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "accounts" in data:
                return data

            if isinstance(data, dict) and data.get("remember"):
                role = str(data.get("role", "user")).strip().lower()
                if role in ("user", "admin"):
                    return {
                        "accounts": {
                            role: {
                                "remember": True,
                                "email": str(data.get("email", "")).strip(),
                            }
                        }
                    }
        except Exception:
            pass
        return {"accounts": {}}

    def load_remembered_login(self, role=None):
        role = role if role in ("user", "admin") else self.role
        self.login_email.clear()
        self.login_password.clear()
        self.remember_checkbox.setChecked(False)

        try:
            data = self.read_remembered_logins()
            account = data.get("accounts", {}).get(role, {})

            if not account.get("remember"):
                return

            email = str(account.get("email", "")).strip()

            if email:
                self.login_email.setText(email)
            self.remember_checkbox.setChecked(True)
        except Exception:
            pass

    def save_remembered_login(self, email):
        os.makedirs(os.path.dirname(REMEMBER_LOGIN_FILE), exist_ok=True)
        data = self.read_remembered_logins()
        accounts = data.setdefault("accounts", {})

        if not self.remember_checkbox.isChecked():
            accounts.pop(self.role, None)
            if accounts:
                with open(REMEMBER_LOGIN_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif os.path.exists(REMEMBER_LOGIN_FILE):
                os.remove(REMEMBER_LOGIN_FILE)
            return

        accounts[self.role] = {
            "remember": True,
            "email": email,
        }

        with open(REMEMBER_LOGIN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def open_app(self):
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if email == "" or password == "":
            QMessageBox.warning(self, "UPLOWER", "Vui lòng nhập email và mật khẩu!")
            return

        try:
            user = auth_manager.authenticate(email, password, expected_role=self.role)
        except ValueError as e:
            QMessageBox.warning(self, "UPLOWER", str(e))
            return

        self.save_remembered_login(email)

        if self.role == "admin":
            self.app_window = AdminUI(current_user=user)
        else:
            self.app_window = ClientUI(current_user=user)

        self.app_window.show()
        self.close()

    def register(self):
        name = self.fullname.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text().strip()
        confirm = self.confirm_password.text().strip()

        if name == "" or email == "" or password == "" or confirm == "":
            QMessageBox.warning(self, "UPLOWER", "Vui lòng nhập đầy đủ thông tin!")
            return

        if password != confirm:
            QMessageBox.warning(self, "UPLOWER", "Mật khẩu xác nhận không khớp!")
            return

        if not self.agree.isChecked():
            QMessageBox.warning(self, "UPLOWER", "Vui lòng đồng ý điều khoản!")
            return

        try:
            auth_manager.create_user(name, email, password, role="user")
        except ValueError as e:
            QMessageBox.warning(self, "UPLOWER", str(e))
            return

        QMessageBox.information(self, "UPLOWER", "Đăng ký thành công. Vui lòng đăng nhập.")
        self.login_email.setText(email)
        self.login_password.clear()
        self.show_login()
