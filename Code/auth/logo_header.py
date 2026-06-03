from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LogoHeader(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("LogoHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 48, 0, 28)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("☁")
        icon.setAlignment(Qt.AlignCenter)
        icon.setObjectName("LogoIcon")

        title = QLabel("UPLOWER")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("LogoTitle")

        subtitle = QLabel("Upload Single File Control System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("LogoSubtitle")

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.setStyleSheet("""
            QWidget#LogoHeader {
                background-color: #080014;
                border-bottom: 1px solid #9C27FF;
            }

            QLabel#LogoIcon {
                min-width: 62px;
                max-width: 62px;
                min-height: 62px;
                max-height: 62px;
                border-radius: 20px;
                color: white;
                font-size: 30px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8A35FF,
                    stop:1 #FF1493
                );
            }

            QLabel#LogoTitle {
                color: #E879F9;
                font-size: 36px;
                font-weight: 900;
                letter-spacing: 1px;
            }

            QLabel#LogoSubtitle {
                color: #CFE8FF;
                font-size: 14px;
            }
        """)