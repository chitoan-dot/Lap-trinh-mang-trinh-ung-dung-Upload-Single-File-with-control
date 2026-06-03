import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def create_window(mode):
    if mode == "client":
        from client.ui_client import ClientUI
        return ClientUI()
    if mode == "server":
        from server.server_monitor_ui import ServerMonitorUI
        return ServerMonitorUI()
    if mode == "admin":
        from admin.ui_admin import AdminUI
        return AdminUI()

    from auth.login_ui import LoginUI
    return LoginUI()


def run_pyqt_app(mode):
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = create_window(mode)
    window.show()
    return app.exec_()


def main():
    parser = argparse.ArgumentParser(description="UPLOWER desktop upload app")
    parser.add_argument("mode", nargs="?", choices=["login", "client", "server", "admin"], default="login")
    args = parser.parse_args()

    try:
        sys.exit(run_pyqt_app(args.mode))
    except Exception as e:
        print("\n===== LOI KHOI DONG =====")
        print(e)
        input("\nNhan Enter de thoat...")


if __name__ == "__main__":
    main()
