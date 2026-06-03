import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def run_pyqt_app():
    from PyQt5.QtWidgets import QApplication
    from auth.login_ui import LoginUI

    app = QApplication(sys.argv)

    window = LoginUI()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    try:
        sys.exit(run_pyqt_app())
    except Exception as e:
        print("\n===== LỖI KHỞI ĐỘNG =====")
        print(e)
        input("\nNhấn Enter để thoát...")