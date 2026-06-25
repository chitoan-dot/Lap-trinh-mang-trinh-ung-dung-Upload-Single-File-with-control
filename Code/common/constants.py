COLORS = {
    "bg": "#0B111A",
    "surface": "#121A26",
    "surface_2": "#182231",
    "surface_3": "#202C3D",
    "border": "#2C3B50",
    "text": "#F4F7FB",
    "muted": "#A7B6CB",
    "subtle": "#72839B",
    "primary": "#4F8CFF",
    "primary_hover": "#3B73E6",
    "success": "#2ECC71",
    "warning": "#F4B860",
    "danger": "#F05D5E",
    "danger_hover": "#D94A4B",
    "button_text": "#FFFFFF",
    "button_disabled_text": "#D7E2F2",
}

APP_NAME = "Desktop Upload App"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_PORT = 8888
CHUNK_SIZE = 64 * 1024
SERVER_ERROR_OFFSET = (1 << 64) - 1
SERVER_VERIFY_OK = b"V"
SERVER_VERIFY_SKIPPED = b"S"
SERVER_VERIFY_FAILED = b"M"
MIN_FREE_SPACE_BUFFER = 5 * 1024 * 1024
CLIENT_CONFIG_FILE = "config/client_config.json"
SERVER_CONFIG_FILE = "config/server_config.json"
UPLOAD_COMMAND = b"U"
AUTH_COMMAND = b"A"
MULTIPART_COMMAND = b"M"
MULTIPART_INIT = b"I"
MULTIPART_PART = b"C"
MULTIPART_FINALIZE = b"F"
MULTIPART_ABORT = b"A"
MULTIPART_READY = b"R"
MULTIPART_ERROR = b"E"

DUPLICATE_POLICIES = {
    "Tiếp tục nếu còn thiếu": "R",
    "Bỏ qua nếu đã có": "S",
    "Ghi đè": "O",
    "Đổi tên tự động": "N",
}
