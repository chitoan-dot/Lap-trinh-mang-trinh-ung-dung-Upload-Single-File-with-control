import json
import os
from datetime import datetime


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HISTORY_FILE = os.path.join(BASE_DIR, "config", "client_upload_history.json")


def load_upload_history(user_email=None):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data if isinstance(data, list) else []
                if user_email:
                    email = str(user_email).strip().lower()
                    return [
                        record for record in records
                        if str(record.get("user_email", "")).strip().lower() == email
                    ]
                return records
    except Exception:
        pass
    return []


def save_upload_history(records):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records[:100], f, indent=2, ensure_ascii=False)


def add_upload_record(file_path, file_size, server, status, speed="", message="", user_email="", user_name=""):
    records = load_upload_history()
    records.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": str(user_email or "").strip().lower(),
        "user_name": str(user_name or "").strip(),
        "file_name": os.path.basename(file_path) if file_path else "",
        "file_path": os.path.abspath(file_path) if file_path else "",
        "file_size": int(file_size or 0),
        "server": server,
        "status": status,
        "speed": speed,
        "message": message,
    })
    save_upload_history(records)


def clear_upload_history(user_email=None):
    if not user_email:
        save_upload_history([])
        return

    email = str(user_email).strip().lower()
    records = [
        record for record in load_upload_history()
        if str(record.get("user_email", "")).strip().lower() != email
    ]
    save_upload_history(records)
