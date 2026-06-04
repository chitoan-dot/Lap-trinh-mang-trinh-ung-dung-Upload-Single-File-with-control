import socket


class SocketClient:
    def __init__(self, host: str, port: int, timeout: float = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    @property
    def address(self):
        return (self.host, self.port)

    def create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock = self.create_socket()
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.address)
        self.sock.settimeout(None)
        return self.sock

    def close(self):
        if not self.sock:
            return
        try:
            self.sock.close()
        finally:
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.close()