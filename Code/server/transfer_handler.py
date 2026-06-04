
import os
import shutil
from common.constants import CHUNK_SIZE, MIN_FREE_SPACE_BUFFER, SERVER_ERROR_OFFSET
from common.protocol import receive_upload_header, send_offset
from common.utils import sanitize_subfolder, unique_file_path


class TransferHandler:
    def __init__(self, upload_dir):
        self.upload_dir = os.path.abspath(upload_dir)

    def prepare_destination(self, sock):
        header = receive_upload_header(sock)
        final_dir, safe_name, file_path = self.resolve_destination(header)
        file_path, offset = self.apply_duplicate_policy(file_path, final_dir, safe_name, header)
        self.ensure_capacity(sock, final_dir, header.file_size, offset)
        send_offset(sock, offset)
        return header, file_path, offset

    def resolve_destination(self, header):
        safe_dir = sanitize_subfolder(header.target_dir)
        final_dir = os.path.join(self.upload_dir, safe_dir)
        os.makedirs(final_dir, exist_ok=True)
        safe_name = os.path.basename(header.file_name)
        file_path = os.path.join(final_dir, safe_name)
        return final_dir, safe_name, file_path

    def apply_duplicate_policy(self, file_path, final_dir, safe_name, header):
        offset = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        if os.path.exists(file_path) and header.duplicate_policy == "O":
            offset = 0
        elif os.path.exists(file_path) and header.duplicate_policy == "N":
            file_path = unique_file_path(final_dir, safe_name)
            offset = 0
        elif os.path.exists(file_path) and header.duplicate_policy == "S":
            offset = header.file_size
        return file_path, offset

    def ensure_capacity(self, sock, final_dir, file_size, offset):
        remaining = max(file_size - offset, 0)
        if remaining > 0 and shutil.disk_usage(final_dir).free < remaining + MIN_FREE_SPACE_BUFFER:
            send_offset(sock, SERVER_ERROR_OFFSET)
            raise RuntimeError("Máy chủ không đủ dung lượng lưu trữ.")
    def receive_file(self, sock, file_path, file_size, offset=0, on_chunk=None):
        mode = "ab" if offset else "wb"
        received = offset
        with open(file_path, mode) as f:
            while received < file_size:
                data = sock.recv(min(CHUNK_SIZE, file_size - received))
                if not data:
                    raise ConnectionError("Client ngắt kết nối khi đang gửi file.")
                self.write_chunk(f, data)
                received += len(data)
                if on_chunk:
                    on_chunk(received, len(data))
        return received

    def write_chunk(self, file_obj, data):
        file_obj.write(data)
