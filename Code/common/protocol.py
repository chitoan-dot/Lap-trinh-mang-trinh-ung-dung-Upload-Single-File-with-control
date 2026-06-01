import struct
from dataclasses import dataclass
from common.constants import UPLOAD_COMMAND
from common.utils import recv_exact


@dataclass
class UploadHeader:
    # Thông tin mô tả một lần gửi file từ client sang server.
    target_dir: str
    file_name: str
    file_size: int
    duplicate_policy: str


def send_upload_header(sock, header: UploadHeader):
    # Gửi mã lệnh để server biết đây là yêu cầu upload file.
    sock.sendall(UPLOAD_COMMAND)

    # Chuyển tên thư mục và tên file sang bytes để truyền qua socket.
    target_bytes = header.target_dir.encode("utf-8")
    file_name_bytes = header.file_name.encode("utf-8")

    # Gửi độ dài thư mục trước, sau đó mới gửi nội dung thư mục.
    sock.sendall(struct.pack("!I", len(target_bytes)))
    sock.sendall(target_bytes)

    # Gửi độ dài tên file trước, sau đó mới gửi nội dung tên file.
    sock.sendall(struct.pack("!I", len(file_name_bytes)))
    sock.sendall(file_name_bytes)

    # Gửi kích thước file bằng 8 bytes để hỗ trợ file lớn.
    sock.sendall(struct.pack("!Q", header.file_size))

    # Gửi chính sách xử lý file trùng tên: R, S, O hoặc N.
    sock.sendall(header.duplicate_policy.encode("utf-8")[:1])


def receive_upload_header(sock) -> UploadHeader:
    # Đọc và kiểm tra mã lệnh đầu tiên từ client.
    command = recv_exact(sock, 1)
    if command != UPLOAD_COMMAND:
        raise ValueError(f"Lệnh không hợp lệ: {command!r}")

    # Đọc thư mục đích mà client muốn lưu file trên server.
    dir_len = struct.unpack("!I", recv_exact(sock, 4))[0]
    target_dir = recv_exact(sock, dir_len).decode("utf-8", errors="replace") if dir_len else ""

    # Đọc tên file gốc.
    name_len = struct.unpack("!I", recv_exact(sock, 4))[0]
    file_name = recv_exact(sock, name_len).decode("utf-8", errors="replace")

    # Đọc kích thước file và chính sách xử lý file trùng.
    file_size = struct.unpack("!Q", recv_exact(sock, 8))[0]
    duplicate_policy = recv_exact(sock, 1).decode("utf-8", errors="replace") or "R"
    return UploadHeader(target_dir, file_name, file_size, duplicate_policy)


def send_offset(sock, offset: int):
    # Server gửi vị trí byte cần client tiếp tục gửi từ đó.
    sock.sendall(struct.pack("!Q", offset))


def receive_offset(sock) -> int:
    # Client nhận offset từ server để biết cần gửi mới hay resume.
    return struct.unpack("!Q", recv_exact(sock, 8))[0]
