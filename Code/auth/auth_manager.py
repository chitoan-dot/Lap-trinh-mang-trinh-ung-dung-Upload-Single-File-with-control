import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime

try:
    from Database.sql_server_sync import (
        sync_user_to_sql_server,
        sync_login_to_sql_server
    )
except Exception:
    sync_user_to_sql_server = None
    sync_login_to_sql_server = None


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "Database", "users.db")

DEFAULT_ADMIN_EMAIL = "admin@uplower.local"
DEFAULT_ADMIN_PASSWORD = "admin123"


class AuthManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
        self.ensure_default_admin()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
                """
            )
            conn.commit()

    def ensure_default_admin(self):
        if self.get_user_by_email(DEFAULT_ADMIN_EMAIL):
            return

        self.create_user(
            full_name="Administrator",
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            role="admin",
        )

    def hash_password(self, password, salt=None):
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()
        return digest, salt

    def verify_password(self, password, password_hash, salt):
        digest, _salt = self.hash_password(password, salt)
        return secrets.compare_digest(digest, password_hash)

    def create_user(self, full_name, email, password, role="user"):
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        role = (role or "user").strip().lower()

        if not full_name:
            raise ValueError("Vui lòng nhập họ và tên.")
        if not email or "@" not in email:
            raise ValueError("Email không hợp lệ.")
        if role not in ("user", "admin"):
            raise ValueError("Vai trò không hợp lệ.")
        if len(password or "") < 4:
            raise ValueError("Mật khẩu phải có ít nhất 4 ký tự.")
        if self.get_user_by_email(email):
            raise ValueError("Email này đã tồn tại.")

        password_hash, salt = self.hash_password(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (full_name, email, role, password_hash, salt, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'Active', ?)
                """,
                (full_name, email, role, password_hash, salt, now),
            )
            conn.commit()

        if sync_user_to_sql_server:
            try:
                sync_user_to_sql_server(
                    full_name=full_name,
                    email=email,
                    password_hash=password_hash,
                    salt=salt,
                    role=role,
                    status="Active"
                )
            except Exception as e:
                print("Không thể đồng bộ user sang SQL Server:", e)

        return self.get_user_by_email(email)

    def authenticate(self, email, password, expected_role=None):
        user = self.get_user_by_email(email)

        if not user:
            raise ValueError("Tài khoản không tồn tại.")
        if expected_role and user["role"] != expected_role:
            raise ValueError("Tài khoản không đúng vai trò đã chọn.")
        if user["status"] != "Active":
            raise ValueError("Tài khoản đang bị khóa.")
        if not self.verify_password(password, user["password_hash"], user["salt"]):
            raise ValueError("Mật khẩu không đúng.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (now, user["id"])
            )
            conn.commit()

        if sync_login_to_sql_server:
            try:
                sync_login_to_sql_server(email)
            except Exception as e:
                print("Không thể đồng bộ login sang SQL Server:", e)

        return self.public_user(self.get_user_by_email(user["email"]))

    def reset_password(self, email, new_password):
        email = (email or "").strip().lower()
        if len(new_password or "") < 4:
            raise ValueError("Mật khẩu mới phải có ít nhất 4 ký tự.")

        user = self.get_user_by_email(email)
        if not user:
            raise ValueError("Tài khoản không tồn tại.")

        password_hash, salt = self.hash_password(new_password)
        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (password_hash, salt, user["id"]),
            )
            conn.commit()

        if sync_user_to_sql_server:
            try:
                sync_user_to_sql_server(
                    full_name=user["full_name"],
                    email=user["email"],
                    password_hash=password_hash,
                    salt=salt,
                    role=user["role"],
                    status=user["status"],
                )
            except Exception as e:
                print("Không thể đồng bộ mật khẩu mới sang SQL Server:", e)

        return self.public_user(self.get_user_by_email(email))
    def get_user_by_email(self, email):
        email = (email or "").strip().lower()

        if not email:
            return None

        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            return dict(row) if row else None

    def list_users(self):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, full_name, email, role, status, created_at, last_login
                FROM users
                ORDER BY role = 'admin' DESC, created_at ASC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def public_user(self, user):
        if not user:
            return None

        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"],
            "created_at": user["created_at"],
            "last_login": user.get("last_login"),
        }


auth_manager = AuthManager()