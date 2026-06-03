from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt

from layout.theme import *

APP_W = 1100
APP_H = 760


class RegisterUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UPLOWER - Đăng ký")
        self.resize(APP_W, APP_H)
        self.setMinimumSize(900, 760)
        self.role = "user"

        self.setStyleSheet(f"""
        QWidget {{
            background:{BG};
            color:{TEXT};
            font-family: Segoe UI, Arial;
        }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
        QScrollArea {
            border:none;
            background:transparent;
        }
        QScrollBar:vertical {
            width:8px;
            background:transparent;
        }
        QScrollBar::handle:vertical {
            background:#334155;
            border-radius:4px;
        }
        """)

        content = QWidget()
        main = QVBoxLayout(content)
        main.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        main.setContentsMargins(0, 25, 0, 25)

        wrap = QFrame()
        wrap.setFixedWidth(560)
        wrap.setStyleSheet("background:transparent; border:none;")

        box = QVBoxLayout(wrap)
        box.setSpacing(8)
        box.setContentsMargins(0, 0, 0, 0)

        logo = QLabel("☁")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(54, 54)
        logo.setStyleSheet(f"""
            background:{GRADIENT};
            color:white;
            border-radius:18px;
            font-size:25px;
            font-weight:bold;
        """)

        title = QLabel("Đăng ký tài khoản")
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(42)
        title.setStyleSheet("""
            color:#d66cff;
            font-size:30px;
            font-weight:900;
        """)

        sub = QLabel("Tạo tài khoản mới để sử dụng UPLOWER")
        sub.setAlignment(Qt.AlignCenter)
        sub.setMinimumHeight(24)
        sub.setStyleSheet(f"color:{TEXT2}; font-size:14px;")

        role_row = QHBoxLayout()
        role_row.setSpacing(15)

        self.user_btn = QPushButton("👤\nUser")
        self.admin_btn = QPushButton("🧑‍💼\nAdmin")

        self.user_btn.setFixedHeight(62)
        self.admin_btn.setFixedHeight(62)

        self.user_btn.clicked.connect(lambda: self.set_role("user"))
        self.admin_btn.clicked.connect(lambda: self.set_role("admin"))

        role_row.addWidget(self.user_btn)
        role_row.addWidget(self.admin_btn)

        self.fullname = self.create_input("👤  Nhập họ và tên")
        self.email = self.create_input("✉  Nhập email")
        self.password = self.create_input("🔒  Nhập mật khẩu", True)
        self.confirm = self.create_input("🔒  Nhập lại mật khẩu", True)

        self.agree = QCheckBox("Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật")
        self.agree.setMinimumHeight(26)
        self.agree.setStyleSheet(f"""
        QCheckBox {{
            color:{TEXT};
            font-size:14px;
            font-weight:bold;
        }}
        QCheckBox::indicator {{
            width:15px;
            height:15px;
        }}
        """)

        register_btn = QPushButton("Đăng ký")
        register_btn.setFixedHeight(46)
        register_btn.setStyleSheet(f"""
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
        """)
        register_btn.clicked.connect(self.register)

        login_btn = QPushButton("Đã có tài khoản? Đăng nhập ngay")
        login_btn.setFixedHeight(36)
        login_btn.setStyleSheet("""
        QPushButton {
            background:transparent;
            border:none;
            color:#d66cff;
            font-size:16px;
            font-weight:bold;
        }
        QPushButton:hover {
            color:#ec4899;
        }
        """)
        login_btn.clicked.connect(self.open_login)

        box.addWidget(logo, alignment=Qt.AlignCenter)
        box.addWidget(title)
        box.addWidget(sub)
        box.addSpacing(4)
        box.addLayout(role_row)

        box.addWidget(self.create_label("Họ và tên"))
        box.addWidget(self.fullname)

        box.addWidget(self.create_label("Email"))
        box.addWidget(self.email)

        box.addWidget(self.create_label("Mật khẩu"))
        box.addWidget(self.password)

        box.addWidget(self.create_label("Xác nhận mật khẩu"))
        box.addWidget(self.confirm)

        box.addWidget(self.agree)
        box.addWidget(register_btn)
        box.addWidget(login_btn)

        main.addWidget(wrap)
        scroll.setWidget(content)
        root.addWidget(scroll)

        self.set_role("user")

    def create_label(self, text):
        label = QLabel(text)
        label.setMinimumHeight(20)
        label.setStyleSheet("font-weight:bold; font-size:14px;")
        return label

    def create_input(self, placeholder, password=False):
        line = QLineEdit()
        line.setPlaceholderText(placeholder)
        line.setFixedHeight(44)
        line.setStyleSheet(self.input_style())

        if password:
            line.setEchoMode(QLineEdit.Password)

        return line

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

    def set_role(self, role):
        self.role = role

        active = f"""
        QPushButton {{
            background:#30104d;
            color:white;
            border:1px solid {PRIMARY};
            border-radius:14px;
            font-size:15px;
            font-weight:bold;
        }}
        """

        normal = f"""
        QPushButton {{
            background:{CARD2};
            color:{TEXT2};
            border:1px solid #334155;
            border-radius:14px;
            font-size:15px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            border:1px solid {PRIMARY};
            color:white;
        }}
        """

        self.user_btn.setStyleSheet(active if role == "user" else normal)
        self.admin_btn.setStyleSheet(active if role == "admin" else normal)

    def register(self):
        name = self.fullname.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        confirm = self.confirm.text().strip()

        if name == "" or email == "" or password == "" or confirm == "":
            QMessageBox.warning(self, "UPLOWER", "Vui lòng nhập đầy đủ thông tin!")
            return

        if password != confirm:
            QMessageBox.warning(self, "UPLOWER", "Mật khẩu xác nhận không khớp!")
            return

        if not self.agree.isChecked():
            QMessageBox.warning(self, "UPLOWER", "Vui lòng đồng ý điều khoản!")
            return

        QMessageBox.information(self, "UPLOWER", "Đăng ký thành công!")
        self.open_login()

    def open_login(self):
        from auth.login_ui import LoginUI

        geometry = self.geometry()
        state = self.windowState()

        self.login_window = LoginUI()
        self.login_window.setGeometry(geometry)
        self.login_window.setWindowState(state)
        self.login_window.show()
        self.close()
