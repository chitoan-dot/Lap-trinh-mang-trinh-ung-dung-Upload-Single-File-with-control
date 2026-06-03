from PyQt5.QtWidgets import QWidget,QVBoxLayout,QLabel,QFrame,QPushButton,QHBoxLayout
class AdminSecurityUI(QWidget):
    def __init__(self):
        super().__init__(); lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20)
        for text in ['🛡 Bật kiểm tra định dạng file', '🔐 Giới hạn dung lượng upload', '🚫 Chặn file nguy hiểm', '📜 Ghi log hoạt động user']:
            f=QFrame(); f.setObjectName('Card'); r=QHBoxLayout(f); r.addWidget(QLabel(text)); r.addStretch(); r.addWidget(QPushButton('Cấu hình')); lay.addWidget(f)
        lay.addStretch()
