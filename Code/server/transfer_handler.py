
import os
import shutil
import hashlib
from common.constants import CHUNK_SIZE, MIN_FREE_SPACE_BUFFER, SERVER_ERROR_OFFSET
from common.protocol import receive_upload_header, send_offset
from common.utils import sanitize_subfolder, unique_file_path


class TransferHandler:
    # Xử lý phần nghiệp vụ nhận file và chọn vị trí lưu trên server.
    def __init__(self, upload_dir):
        self.upload_dir = os.path.abspath(upload_dir)

    def prepare_destination(self, sock):
        # Nhận header từ client để biết tên file, thư mục đích, kích thước và policy.
        header = receive_upload_header(sock)

        # Làm sạch thư mục/tên file để tránh ghi ra ngoài thư mục upload.
        safe_dir = sanitize_subfolder(header.target_dir)
        final_dir = os.path.join(self.upload_dir, safe_dir)
        os.makedirs(final_dir, exist_ok=True)
        safe_name = os.path.basename(header.file_name)
        file_path = os.path.join(final_dir, safe_name)
        offset = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Áp dụng chính sách xử lý khi file đã tồn tại trên server.
        if os.path.exists(file_path) and header.duplicate_policy == "O":
            offset = 0
        elif os.path.exists(file_path) and header.duplicate_policy == "N":
            file_path = unique_file_path(final_dir, safe_name)
            offset = 0
        elif os.path.exists(file_path) and header.duplicate_policy == "S":
            offset = header.file_size
        elif os.path.exists(file_path) and offset >= header.file_size:
            if self.calculate_file_hash(file_path) != header.file_hash:
                offset = 0

        # Kiểm tra dung lượng trống trước khi cho client bắt đầu gửi dữ liệu.
        remaining = max(header.file_size - offset, 0)
        if remaining > 0 and shutil.disk_usage(final_dir).free < remaining + MIN_FREE_SPACE_BUFFER:
            send_offset(sock, SERVER_ERROR_OFFSET)
            raise RuntimeError("Máy chủ không đủ dung lượng lưu trữ.")
        send_offset(sock, offset)
        return header, file_path, offset

    def calculate_file_hash(self, file_path):
        digest = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.digest()

    def receive_file(self, sock, file_path, file_size, offset=0, on_chunk=None):
        # Ghi tiếp nếu đang resume, hoặc ghi mới nếu offset bằng 0.
        mode = "ab" if offset else "wb"
        received = offset
        with open(file_path, mode) as f:
            while received < file_size:
                # Nhận từng chunk từ client để xử lý được file lớn.
                data = sock.recv(min(CHUNK_SIZE, file_size - received))
                if not data:
                    raise ConnectionError("Client ngắt kết nối khi đang gửi file.")
                f.write(data)
                received += len(data)
                if on_chunk:
                    on_chunk(received, len(data))
        return received
