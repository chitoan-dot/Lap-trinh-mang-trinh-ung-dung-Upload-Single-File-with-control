from datetime import datetime


class AppLogger:
    def __init__(self, callback=None):
        self.callback = callback

    def log(self, message, level="INFO"):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
        if self.callback:
            self.callback(line, level)
        else:
            print(line)
