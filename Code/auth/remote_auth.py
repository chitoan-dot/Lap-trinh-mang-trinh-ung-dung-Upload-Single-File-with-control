import socket

from common.config import client_server_address
from common.constants import AUTH_COMMAND
from common.protocol import receive_json_message, send_json_message


class RemoteAuthError(ValueError):
    pass


def request_auth(action, host=None, port=None, timeout=5, **payload):
    host, port = (host, port) if host and port else client_server_address()
    request = {"action": action, **payload}

    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as sock:
            sock.sendall(AUTH_COMMAND)
            send_json_message(sock, request)
            response = receive_json_message(sock)
    except OSError as e:
        raise RemoteAuthError(
            f"Không kết nối được Server xác thực tại {host}:{port}. "
            "Hãy bật Server và kiểm tra Code/config/client_config.json."
        ) from e

    if not isinstance(response, dict):
        raise RemoteAuthError("Server xác thực trả về dữ liệu không hợp lệ.")
    if not response.get("ok"):
        raise RemoteAuthError(response.get("error") or "Yêu cầu xác thực thất bại.")
    return response.get("data")


def authenticate(email, password, expected_role=None, host=None, port=None):
    return request_auth(
        "authenticate",
        host=host,
        port=port,
        email=email,
        password=password,
        expected_role=expected_role,
    )


def create_user(full_name, email, password, role="user", host=None, port=None):
    return request_auth(
        "create_user",
        host=host,
        port=port,
        full_name=full_name,
        email=email,
        password=password,
        role=role,
    )


def get_user_by_email(email, host=None, port=None):
    return request_auth("get_user_by_email", host=host, port=port, email=email)


def reset_password(email, new_password, host=None, port=None):
    return request_auth(
        "reset_password",
        host=host,
        port=port,
        email=email,
        new_password=new_password,
    )
