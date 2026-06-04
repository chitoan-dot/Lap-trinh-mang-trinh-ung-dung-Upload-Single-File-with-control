import os
import hashlib
import time
from common.constants import CHUNK_SIZE, SERVER_VERIFY_FAILED, SERVER_VERIFY_OK, SERVER_VERIFY_SKIPPED
from common.protocol import UploadHeader, send_upload_header, receive_offset
from common.utils import recv_exact


HASH_CHUNK_SIZE = 1024 * 1024
PAUSE_DELAY = 0.1
THROTTLE_DELAY = 0.05
VALID_VERIFY_STATUSES = (SERVER_VERIFY_OK, SERVER_VERIFY_SKIPPED)


class UploadManager:
    def __init__(self, sock):
        self.sock = sock

    def prepare_upload(self, file_path, target_dir, duplicate_policy):
        header = self.build_header(file_path, target_dir, duplicate_policy)
        send_upload_header(self.sock, header)
        return receive_offset(self.sock)

    def build_header(self, file_path, target_dir, duplicate_policy):
        return UploadHeader(
            target_dir=target_dir,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            duplicate_policy=duplicate_policy,
            file_hash=self.calculate_file_hash(file_path),
        )

    def calculate_file_hash(self, file_path):
        digest = hashlib.sha256()
        for chunk in self.read_chunks(file_path, HASH_CHUNK_SIZE):
            digest.update(chunk)
        return digest.digest()

    def read_chunks(self, file_path, chunk_size=CHUNK_SIZE, offset=0):
        with open(file_path, "rb") as f:
            if offset:
                f.seek(offset)
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    return
                yield chunk

    def receive_verify_status(self):
        status = recv_exact(self.sock, 1)
        if status == SERVER_VERIFY_FAILED:
            raise RuntimeError("Checksum không khớp sau khi upload.")
        if status not in VALID_VERIFY_STATUSES:
            raise RuntimeError("Server trả về trạng thái xác minh không hợp lệ.")
        return status

    def stream_file(self, file_path, offset=0, on_chunk=None, should_stop=None, should_pause=None, speed_limit=0):
        sent = offset
        session_sent = 0
        session_start = time.time()

        for data in self.read_chunks(file_path, CHUNK_SIZE, offset):
            if self.is_requested(should_stop):
                break
            if self.wait_if_paused(should_pause, should_stop):
                return sent

            self.sock.sendall(data)
            sent += len(data)
            session_sent += len(data)
            self.throttle(session_start, session_sent, speed_limit, should_stop, should_pause)
            if on_chunk:
                on_chunk(sent, len(data))
        return sent

    def is_requested(self, callback):
        return bool(callback and callback())

    def wait_if_paused(self, should_pause=None, should_stop=None):
        while self.is_requested(should_pause):
            if self.is_requested(should_stop):
                return True
            time.sleep(PAUSE_DELAY)
        return False

    def throttle(self, session_start, session_sent, speed_limit, should_stop=None, should_pause=None):
        if speed_limit <= 0:
            return
        expected_elapsed = session_sent / speed_limit
        while True:
            if self.is_requested(should_stop):
                return
            if self.is_requested(should_pause):
                return
            sleep_time = expected_elapsed - (time.time() - session_start)
            if sleep_time <= 0:
                return
            time.sleep(min(sleep_time, THROTTLE_DELAY))
