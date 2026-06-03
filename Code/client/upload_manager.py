import os
import hashlib
import time
from common.constants import CHUNK_SIZE, SERVER_VERIFY_FAILED, SERVER_VERIFY_OK, SERVER_VERIFY_SKIPPED
from common.protocol import UploadHeader, send_upload_header, receive_offset
from common.utils import recv_exact


class UploadManager:
    def __init__(self, sock):
        self.sock = sock

    def prepare_upload(self, file_path, target_dir, duplicate_policy):
        file_hash = self.calculate_file_hash(file_path)
        header = UploadHeader(
            target_dir=target_dir,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            duplicate_policy=duplicate_policy,
            file_hash=file_hash,
        )
        send_upload_header(self.sock, header)
        return receive_offset(self.sock)

    def calculate_file_hash(self, file_path):
        digest = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.digest()

    def receive_verify_status(self):
        status = recv_exact(self.sock, 1)
        if status == SERVER_VERIFY_FAILED:
            raise RuntimeError("Checksum không khớp sau khi upload.")
        if status not in (SERVER_VERIFY_OK, SERVER_VERIFY_SKIPPED):
            raise RuntimeError("Server trả về trạng thái xác minh không hợp lệ.")
        return status

    def stream_file(self, file_path, offset=0, on_chunk=None, should_stop=None, should_pause=None, speed_limit=0):
        sent = offset
        session_sent = 0
        session_start = time.time()
        with open(file_path, "rb") as f:
            f.seek(offset)
            while True:
                if should_stop and should_stop():
                    break
                while should_pause and should_pause():
                    if should_stop and should_stop():
                        return sent
                    time.sleep(0.1)
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                self.sock.sendall(data)
                sent += len(data)
                session_sent += len(data)
                self.throttle(session_start, session_sent, speed_limit, should_stop, should_pause)
                if on_chunk:
                    on_chunk(sent, len(data))
        return sent

    def throttle(self, session_start, session_sent, speed_limit, should_stop=None, should_pause=None):
        if speed_limit <= 0:
            return
        expected_elapsed = session_sent / speed_limit
        while True:
            if should_stop and should_stop():
                return
            if should_pause and should_pause():
                return
            sleep_time = expected_elapsed - (time.time() - session_start)
            if sleep_time <= 0:
                return
            time.sleep(min(sleep_time, 0.05))
