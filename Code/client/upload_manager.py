import os
import hashlib
import struct
import time
from common.constants import (
    CHUNK_SIZE,
    MULTIPART_ABORT,
    MULTIPART_COMMAND,
    MULTIPART_ERROR,
    MULTIPART_FINALIZE,
    MULTIPART_INIT,
    MULTIPART_PART,
    MULTIPART_READY,
    SERVER_VERIFY_FAILED,
    SERVER_VERIFY_OK,
    SERVER_VERIFY_SKIPPED,
)
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

    def prepare_multipart_upload(self, file_path, target_dir, duplicate_policy, part_count):
        file_hash = self.calculate_file_hash(file_path)
        target_bytes = target_dir.encode("utf-8")
        file_name_bytes = os.path.basename(file_path).encode("utf-8")

        self.sock.sendall(MULTIPART_COMMAND)
        self.sock.sendall(MULTIPART_INIT)
        self.sock.sendall(struct.pack("!I", len(target_bytes)))
        self.sock.sendall(target_bytes)
        self.sock.sendall(struct.pack("!I", len(file_name_bytes)))
        self.sock.sendall(file_name_bytes)
        self.sock.sendall(struct.pack("!Q", os.path.getsize(file_path)))
        self.sock.sendall(duplicate_policy.encode("utf-8")[:1])
        self.sock.sendall(file_hash)
        self.sock.sendall(struct.pack("!H", int(part_count)))

        status = recv_exact(self.sock, 1)
        if status == MULTIPART_ERROR:
            msg_len = struct.unpack("!I", recv_exact(self.sock, 4))[0]
            message = recv_exact(self.sock, msg_len).decode("utf-8", errors="replace") if msg_len else ""
            raise RuntimeError(message or "Server từ chối khởi tạo multi-part upload.")
        if status == SERVER_VERIFY_SKIPPED:
            return None
        if status != MULTIPART_READY:
            raise RuntimeError("Server trả về trạng thái multi-part không hợp lệ.")

        session_len = struct.unpack("!I", recv_exact(self.sock, 4))[0]
        return recv_exact(self.sock, session_len).decode("utf-8", errors="replace")

    def upload_multipart_part(
        self,
        file_path,
        session_id,
        part_index,
        offset,
        part_size,
        on_chunk=None,
        should_stop=None,
        should_pause=None,
        speed_limit=0,
    ):
        session_bytes = session_id.encode("utf-8")
        self.sock.sendall(MULTIPART_COMMAND)
        self.sock.sendall(MULTIPART_PART)
        self.sock.sendall(struct.pack("!I", len(session_bytes)))
        self.sock.sendall(session_bytes)
        self.sock.sendall(struct.pack("!HQQ", int(part_index), int(offset), int(part_size)))

        sent = 0
        session_sent = 0
        session_start = time.time()
        with open(file_path, "rb") as f:
            f.seek(offset)
            while sent < part_size:
                if should_stop and should_stop():
                    return False
                while should_pause and should_pause():
                    if should_stop and should_stop():
                        return False
                    time.sleep(0.1)
                data = f.read(min(CHUNK_SIZE, part_size - sent))
                if not data:
                    break
                self.sock.sendall(data)
                sent += len(data)
                session_sent += len(data)
                self.throttle(session_start, session_sent, speed_limit, should_stop, should_pause)
                if on_chunk:
                    on_chunk(part_index, sent, len(data))

        if sent != part_size:
            return False
        status = recv_exact(self.sock, 1)
        if status != SERVER_VERIFY_OK:
            raise RuntimeError(f"Server không xác nhận part {part_index + 1}.")
        return True

    def finalize_multipart_upload(self, session_id):
        session_bytes = session_id.encode("utf-8")
        self.sock.sendall(MULTIPART_COMMAND)
        self.sock.sendall(MULTIPART_FINALIZE)
        self.sock.sendall(struct.pack("!I", len(session_bytes)))
        self.sock.sendall(session_bytes)
        return self.receive_verify_status()

    def abort_multipart_upload(self, session_id):
        session_bytes = session_id.encode("utf-8")
        self.sock.sendall(MULTIPART_COMMAND)
        self.sock.sendall(MULTIPART_ABORT)
        self.sock.sendall(struct.pack("!I", len(session_bytes)))
        self.sock.sendall(session_bytes)
        return recv_exact(self.sock, 1)

