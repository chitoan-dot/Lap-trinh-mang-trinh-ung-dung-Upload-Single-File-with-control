import os
import time
from common.constants import CHUNK_SIZE
from common.protocol import UploadHeader, send_upload_header, receive_offset


class UploadManager:
    def __init__(self, sock):
        self.sock = sock

    def prepare_upload(self, file_path, target_dir, duplicate_policy):
        header = UploadHeader(
            target_dir=target_dir,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            duplicate_policy=duplicate_policy,
        )
        send_upload_header(self.sock, header)
        return receive_offset(self.sock)

    def stream_file(self, file_path, offset=0, on_chunk=None, should_stop=None, should_pause=None):
        sent = offset
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
                if on_chunk:
                    on_chunk(sent, len(data))
        return sent
