import struct
from dataclasses import dataclass
from common.constants import UPLOAD_COMMAND
from common.utils import recv_exact


@dataclass
class UploadHeader:
    target_dir: str
    file_name: str
    file_size: int
    duplicate_policy: str
    file_hash: bytes = b""


def send_upload_header(sock, header: UploadHeader):
    sock.sendall(UPLOAD_COMMAND)
    target_bytes = header.target_dir.encode("utf-8")
    file_name_bytes = header.file_name.encode("utf-8")
    sock.sendall(struct.pack("!I", len(target_bytes)))
    sock.sendall(target_bytes)
    sock.sendall(struct.pack("!I", len(file_name_bytes)))
    sock.sendall(file_name_bytes)
    sock.sendall(struct.pack("!Q", header.file_size))
    sock.sendall(header.duplicate_policy.encode("utf-8")[:1])
    sock.sendall(header.file_hash)


def receive_upload_header(sock) -> UploadHeader:
    command = recv_exact(sock, 1)
    if command != UPLOAD_COMMAND:
        raise ValueError(f"Lệnh không hợp lệ: {command!r}")
    dir_len = struct.unpack("!I", recv_exact(sock, 4))[0]
    target_dir = recv_exact(sock, dir_len).decode("utf-8", errors="replace") if dir_len else ""
    name_len = struct.unpack("!I", recv_exact(sock, 4))[0]
    file_name = recv_exact(sock, name_len).decode("utf-8", errors="replace")
    file_size = struct.unpack("!Q", recv_exact(sock, 8))[0]
    duplicate_policy = recv_exact(sock, 1).decode("utf-8", errors="replace") or "R"
    file_hash = recv_exact(sock, 32)
    return UploadHeader(target_dir, file_name, file_size, duplicate_policy, file_hash)


def send_offset(sock, offset: int):
    sock.sendall(struct.pack("!Q", offset))


def receive_offset(sock) -> int:
    return struct.unpack("!Q", recv_exact(sock, 8))[0]
