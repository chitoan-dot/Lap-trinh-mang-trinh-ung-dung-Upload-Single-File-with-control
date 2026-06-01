import argparse
import os
import sys

# Đưa thư mục Code vào sys.path để các package client/server/common import được nhau.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from client.client_app import run_client
from server.server_app import run_server


def main():
    # Chọn chế độ chạy bằng tham số dòng lệnh: client hoặc server.
    parser = argparse.ArgumentParser(description="Desktop Upload App")
    parser.add_argument("mode", nargs="?", choices=["client", "server"], default="client")
    args = parser.parse_args()

    # Khởi động đúng giao diện theo chế độ người dùng chọn.
    if args.mode == "server":
        run_server()
    else:
        run_client()


if __name__ == "__main__":
    main()
