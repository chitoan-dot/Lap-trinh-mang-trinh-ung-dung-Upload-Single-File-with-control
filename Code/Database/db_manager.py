from auth.auth_manager import auth_manager

try:
    from Database import sql_server_sync as _sql_server_sync
    from Database.sql_server_sync import (
        sync_file_to_sql_server,
        sync_upload_log_to_sql_server,
        get_all_sql_users,
        get_all_sql_files
    )
    if getattr(_sql_server_sync, "pyodbc", None) is None:
        raise ImportError("pyodbc is not available")
except Exception:
    sync_file_to_sql_server = None
    sync_upload_log_to_sql_server = None
    get_all_sql_users = None
    get_all_sql_files = None


# ==========================
# LOGIN / REGISTER
# ==========================

def register_user(
    full_name,
    email,
    password,
    role="user"
):
    return auth_manager.create_user(
        full_name,
        email,
        password,
        role
    )


def check_login(
    email,
    password,
    expected_role=None
):
    return auth_manager.authenticate(
        email,
        password,
        expected_role
    )


# ==========================
# FILE
# ==========================

def save_uploaded_file(
    user_email,
    file_name,
    file_size,
    file_hash,
    file_path,
    status="uploaded"
):
    if not sync_file_to_sql_server:
        return None
    return sync_file_to_sql_server(
        user_email=user_email,
        file_name=file_name,
        file_size=file_size,
        file_hash=file_hash,
        file_path=file_path,
        status=status
    )


# ==========================
# LOG
# ==========================

def save_upload_log(
    user_email,
    action,
    description
):
    if not sync_upload_log_to_sql_server:
        return None
    return sync_upload_log_to_sql_server(
        user_email=user_email,
        action=action,
        description=description
    )


# ==========================
# ADMIN
# ==========================

def get_all_users():
    if not get_all_sql_users:
        return []
    return get_all_sql_users()


def get_all_files():
    if not get_all_sql_files:
        return []
    return get_all_sql_files()
