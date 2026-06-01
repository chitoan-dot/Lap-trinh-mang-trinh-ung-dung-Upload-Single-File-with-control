import socket


class SocketClient:
    # Lớp bọc thao tác kết nối TCP từ client tới server.
    def __init__(self, host: str, port: int, timeout: float = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        # Tạo socket, kết nối tới server, rồi bỏ timeout để truyền file dài.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(None)
        return self.sock

    def close(self):
        # Đóng socket nếu đang mở.
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None
