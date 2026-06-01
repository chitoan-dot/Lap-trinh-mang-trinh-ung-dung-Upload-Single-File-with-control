import os
import socket


def format_bytes(value):
    # Chuyển số byte thành chuỗi dễ đọc như KB, MB, GB.
    value = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024


def format_duration(seconds):
    # Chuyển số giây thành định dạng ngắn để hiển thị ETA.
    if seconds is None:
        return "--"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def recv_exact(sock, size):
    # Đọc đúng số byte yêu cầu từ socket, vì recv có thể trả về ít hơn size.
    chunks = []
    received = 0
    while received < size:
        chunk = sock.recv(size - received)
        if not chunk:
            raise ConnectionError("Kết nối bị đóng khi đang đọc dữ liệu.")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def sanitize_subfolder(folder_name):
    # Làm sạch tên thư mục con để tránh đường dẫn nguy hiểm như ../.
    folder_name = (folder_name or "").strip().replace("\\", "/")
    parts = []
    for part in folder_name.split("/"):
        part = part.strip().strip(".")
        if part:
            parts.append(part)
    return os.path.join(*parts) if parts else ""


def unique_file_path(folder, file_name):
    # Tạo tên file mới nếu file đã tồn tại: file (1).txt, file (2).txt...
    stem, ext = os.path.splitext(file_name)
    candidate = os.path.join(folder, file_name)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem} ({counter}){ext}")
        counter += 1
    return candidate


def get_lan_ip():
    # Lấy IP LAN hiện tại để người dùng dễ cấu hình client kết nối tới server.
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        ip = probe.getsockname()[0]
        probe.close()
        return ip
    except Exception:
        return "127.0.0.1"
