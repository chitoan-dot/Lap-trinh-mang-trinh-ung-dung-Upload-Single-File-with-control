import os
from common.constants import CHUNK_SIZE
from common.protocol import UploadHeader, send_upload_header, receive_offset


class UploadManager:
    # Xử lý phần nghiệp vụ gửi file sau khi socket đã kết nối.
    def __init__(self, sock):
        self.sock = sock

    def prepare_upload(self, file_path, target_dir, duplicate_policy):
        # Gửi header mô tả file và nhận offset từ server để biết có cần resume không.
        header = UploadHeader(
            target_dir=target_dir,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            duplicate_policy=duplicate_policy,
        )
        send_upload_header(self.sock, header)
        return receive_offset(self.sock)

    def stream_file(self, file_path, offset=0, on_chunk=None, should_stop=None, should_pause=None):
        # Gửi nội dung file theo từng chunk để không nạp toàn bộ file vào RAM.
        sent = offset
        with open(file_path, "rb") as f:
            f.seek(offset)
            while True:
                # Cho phép UI dừng phiên gửi khi người dùng bấm Stop.
                if should_stop and should_stop():
                    break
                # Khi pause, vòng lặp chờ cho tới khi người dùng resume hoặc stop.
                while should_pause and should_pause():
                    if should_stop and should_stop():
                        return sent
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                self.sock.sendall(data)
                sent += len(data)
                if on_chunk:
                    on_chunk(sent, len(data))
        return sent
