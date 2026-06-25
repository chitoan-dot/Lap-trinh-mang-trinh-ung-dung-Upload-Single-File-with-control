import json
import os

from common.constants import DEFAULT_HOST, DEFAULT_PORT


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT_CONFIG_PATH = os.path.join(BASE_DIR, "config", "client_config.json")


def load_client_config():
    try:
        if os.path.exists(CLIENT_CONFIG_PATH):
            with open(CLIENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def client_server_address():
    config = load_client_config()
    host = str(config.get("server_ip", DEFAULT_HOST)).strip() or DEFAULT_HOST
    try:
        port = int(config.get("server_port", DEFAULT_PORT))
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    return host, port
