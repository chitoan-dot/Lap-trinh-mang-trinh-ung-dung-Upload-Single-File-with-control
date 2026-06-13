import pyodbc
from datetime import datetime

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "UploaderDB"


def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


def get_sql_user_id_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("select id from users where email = ?", email)
    row = cursor.fetchone()

    conn.close()
    return row.id if row else None


def sync_user_to_sql_server(full_name, email, password_hash, salt, role, status="Active"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("select id from users where email = ?", email)
    row = cursor.fetchone()

    if row:
        cursor.execute(
            """
            update users
            set full_name = ?, password_hash = ?, salt = ?, role = ?, status = ?
            where email = ?
            """,
            full_name,
            password_hash,
            salt,
            role,
            status,
            email
        )
    else:
        cursor.execute(
            """
            insert into users
            (full_name, email, password_hash, salt, role, status, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            full_name,
            email,
            password_hash,
            salt,
            role,
            status,
            datetime.now()
        )

    conn.commit()
    conn.close()


def sync_login_to_sql_server(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        update users
        set last_login = ?
        where email = ?
        """,
        datetime.now(),
        email
    )

    conn.commit()
    conn.close()


def sync_file_to_sql_server(
    user_email,
    file_name,
    file_size,
    file_hash,
    file_path,
    status="uploaded"
):
    user_id = get_sql_user_id_by_email(user_email)

    if not user_id:
        print("Không tìm thấy user trong SQL Server:", user_email)
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        insert into files
        (user_id, file_name, file_size, file_hash, file_path, status, uploaded_at)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        user_id,
        file_name,
        file_size,
        file_hash,
        file_path,
        status,
        datetime.now()
    )

    conn.commit()
    conn.close()


def sync_upload_log_to_sql_server(
    user_email,
    action,
    description
):
    user_id = get_sql_user_id_by_email(user_email)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        insert into upload_logs
        (user_id, action, description, created_at)
        values (?, ?, ?, ?)
        """,
        user_id,
        action,
        description,
        datetime.now()
    )

    conn.commit()
    conn.close()


def get_all_sql_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        select id, full_name, email, role, status, created_at, last_login
        from users
        order by created_at desc
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_sql_files():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        select f.id, f.file_name, f.file_size, f.status, f.uploaded_at, u.email
        from files f
        join users u on f.user_id = u.id
        order by f.uploaded_at desc
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows