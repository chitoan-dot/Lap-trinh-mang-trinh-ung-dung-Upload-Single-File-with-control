from datetime import datetime


class AppLogger:
    # Ghi log ra callback của UI hoặc in ra console nếu không có callback.
    def __init__(self, callback=None):
        self.callback = callback

    def log(self, message, level="INFO"):
        # Gắn thời gian và mức log để dễ theo dõi hoạt động server.
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
        if self.callback:
            self.callback(line, level)
        else:
            print(line)
