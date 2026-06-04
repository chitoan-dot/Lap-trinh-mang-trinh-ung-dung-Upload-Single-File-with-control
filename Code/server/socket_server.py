import socket 

 

class SocketServer: 
     def __init__(self, host: str, port: int, backlog: int = 10): 
        self.host = host 

        self.port = port 

        self.backlog = backlog 

        self.sock = None 

 

    def start(self): 

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        self.sock.bind((self.host, self.port)) 

        self.sock.listen(self.backlog) 

        return self.sock 

 

    def close(self): 

        if self.sock: 

             try: 

                 self.sock.close() 

            finally: 

                self.sock = None 