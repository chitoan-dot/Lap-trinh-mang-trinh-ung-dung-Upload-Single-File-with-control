import socket


class SocketServer:
    def __init__(self, host: str, port: int, backlog: int = 10):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.sock = None

    @property
    def address(self):
        return (self.host, self.port)

    def create_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return server_socket

    def start(self):
        self.sock = self.create_socket()
        self.sock.bind(self.address)
        self.sock.listen(self.backlog)
        return self.sock

    def close(self):
        if not self.sock:
            return
        try:
            self.sock.close()
        finally:
            self.sock = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.close()
