import socket

class SocketClient:
    def __init__(self, host: str, port: int, timeout: float = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(30 if self.timeout >= 10 else self.timeout)
        return self.sock

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None


