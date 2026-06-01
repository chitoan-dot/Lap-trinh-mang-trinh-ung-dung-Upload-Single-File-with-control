import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from client.client_app import run_client
from server.server_app import run_server


def main():
    parser = argparse.ArgumentParser(description="Desktop Upload App")
    parser.add_argument("mode", nargs="?", choices=["client", "server"], default="client")
    args = parser.parse_args()

    if args.mode == "server":
        run_server()
    else:
        run_client()


if __name__ == "__main__":
    main()
