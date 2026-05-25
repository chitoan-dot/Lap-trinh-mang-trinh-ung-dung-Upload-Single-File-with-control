import os


class FileQueue:
    def __init__(self):
        self.paths = []
        self.states = {}

    def add_files(self, files):
        added = []
        for path in files:
            normalized = os.path.abspath(path)
            if os.path.isfile(normalized) and normalized not in self.paths:
                self.paths.append(normalized)
                self.states[normalized] = "Đang chờ"
                added.append(normalized)
        return added

    def pending(self):
        return [p for p in self.paths if self.states.get(p) not in ("Hoàn tất", "Đã bỏ qua")]
