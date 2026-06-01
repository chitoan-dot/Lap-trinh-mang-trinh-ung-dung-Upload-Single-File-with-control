import os


class FileQueue:
    # Quản lý danh sách file mà người dùng đã chọn để gửi.
    def __init__(self):
        self.paths = []
        self.states = {}

    def add_files(self, files):
        # Chỉ thêm file hợp lệ và chưa có trong hàng đợi.
        added = []
        for path in files:
            normalized = os.path.abspath(path)
            if os.path.isfile(normalized) and normalized not in self.paths:
                self.paths.append(normalized)
                self.states[normalized] = "Đang chờ"
                added.append(normalized)
        return added

    def pending(self):
        # Trả về những file chưa hoàn tất hoặc chưa bị bỏ qua.
        return [p for p in self.paths if self.states.get(p) not in ("Hoàn tất", "Đã bỏ qua")]
