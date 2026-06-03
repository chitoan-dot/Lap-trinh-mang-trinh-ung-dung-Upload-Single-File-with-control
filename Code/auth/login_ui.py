from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QStackedWidget,
    QScrollArea
)
from PyQt5.QtCore import Qt

from layout.theme import *
from client.ui_client import ClientUI
from admin.ui_admin import AdminUI


class LoginUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPLOWER - Auth")
        self.resize(1100, 760)
        self.setMinimumSize(900, 760)

        self.role = "user"
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
        self.set_role("user")

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
            """
        return f"""
        QPushButton {{
            background:{CARD2};
            color:{TEXT2};
            border:1px solid #334155;
            border-radius:14px;
            font-weight:bold;
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

        setattr(self, f"{prefix}_user_btn", user_btn)
        setattr(self, f"{prefix}_admin_btn", admin_btn)

        row.addWidget(user_btn)
        row.addWidget(admin_btn)

        return row

    def login_page(self):
        page, box = self.make_page()
        logo, title, sub = self.header(
            "UPLOWER",
            "Upload Single File Control System"
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

        option_row = QHBoxLayout()
        remember = QCheckBox("Ghi nhớ đăng nhập")
        remember.setStyleSheet("font-weight:bold;")

        forgot = QPushButton("Quên mật khẩu?")
        forgot.setStyleSheet(self.link_button_style())
        forgot.clicked.connect(
            lambda: QMessageBox.information(self, "UPLOWER", "Chức năng này sẽ bổ sung sau.")
        )

        option_row.addWidget(remember)
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
            "Đăng Ký Tài Khoản",
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
        self.agree.setStyleSheet("font-weight:bold;")

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

    def show_register(self):
        self.stack.setCurrentIndex(1)
        self.setWindowTitle("UPLOWER - Register")

    def show_login(self):
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("UPLOWER - Login")

    def open_app(self):
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if email == "" or password == "":
            QMessageBox.warning(self, "UPLOWER", "Vui lòng nhập email và mật khẩu!")
            return

        if self.role == "admin":
            self.app_window = AdminUI()
        else:
            self.app_window = ClientUI()

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

        QMessageBox.information(self, "UPLOWER", "Đăng ký thành công! Vui lòng đăng nhập.")
        self.login_email.setText(email)
        self.login_password.clear()
        self.show_login()