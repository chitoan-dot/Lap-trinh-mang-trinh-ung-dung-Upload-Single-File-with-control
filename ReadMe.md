# Upload Single File with Control

## Cấu trúc nộp bài

- `Code/`: Mã nguồn của chương trình.
- `DOCX/`: Báo cáo Word (`.doc`, `.docx`).
- `Extra/`: Minh chứng, hình ảnh, file test upload, tài liệu bổ sung.
- `PPTX/`: Slide thuyết trình (`.ppt`, `.pptx`).

## Cách chạy nhanh

Double-click:

```powershell
run_project.bat
```

File này sẽ mở 2 cửa sổ:

- `Upload Server`: giao diện server PyQt.
- `Upload Client`: giao diện user PyQt.

Trên cửa sổ Server bấm `Bắt đầu`, sau đó bên Client chọn file và bấm `Start`.

Lưu ý: cách này là chế độ chạy nhanh để kiểm thử và demo nhanh chức năng upload file.
Script sẽ mở thẳng Server và Client để tiết kiệm thời gian, nên sẽ bỏ qua bước đăng nhập.
Khi thuyết trình, có thể giải thích rằng terminal chỉ dùng để khởi động tiến trình,
còn chương trình chính vẫn là các cửa sổ desktop app.

## Cách chạy thủ công

Mở terminal tại thư mục project:

```powershell
pip install -r requirements.txt
cd Code
python main.py server
```

Mở terminal khác:

```powershell
cd Code
python main.py client
```

Các chế độ khác:

```powershell
python main.py login
python main.py admin
```

`admin` mở Admin Panel của frontend mới. Khi demo đề tài upload, nên ưu tiên chạy `server` và `client`.

## Cách demo đúng luồng desktop app

Nếu muốn demo đầy đủ hơn, đúng với yêu cầu có desktop app, đăng nhập và phân quyền,
nên bắt đầu từ màn hình login:

```powershell
cd Code
python main.py login
```

Luồng demo gợi ý:

1. Mở `python main.py login`.
2. Đăng nhập admin bằng tài khoản mặc định.
3. Giới thiệu Admin Panel: Dashboard, Users, Files, Analytics, Security, Settings.
4. Mở cửa sổ Server và bấm `Bắt đầu` để server lắng nghe socket.
   - Có thể mở bằng tab/chức năng Server trong Admin Panel nếu đang dùng.
   - Hoặc mở riêng một tiến trình:

```powershell
cd Code
python main.py server
```

5. Mở cửa sổ Client/User để gửi file:

```powershell
cd Code
python main.py client
```

6. Trên Client chọn file, chọn chế độ xử lý file trùng, rồi bấm `Start`.
7. Trong lúc upload có thể demo các nút `Pause`, `Resume`, `Stop`.
8. Sau khi upload xong, quay lại Server để xem log, trạng thái xác minh SHA-256 và file đã nhận.
9. Quay lại Admin Panel để xem danh sách file, thống kê và lịch sử upload.

Giải thích khi demo: đây là mô hình client-server nên Server và Client nên chạy song song.
Việc có 2 cửa sổ desktop là hợp lý vì Server là tiến trình lắng nghe/quản lý kết nối,
còn Client là tiến trình người dùng gửi file. `run_project.bat` chỉ là cách mở nhanh 2 cửa sổ này.

## Tài khoản demo

- Admin mặc định: `admin@uplower.local`
- Mật khẩu admin: `admin123`
- User mới có thể tạo tại màn hình `Đăng ký`.
- Khi đăng nhập phải chọn đúng vai trò. Tài khoản user không thể đăng nhập vào Admin Panel.
- Admin Panel đã đọc dữ liệu thật:
  - `Dashboard`: tổng user, file, dung lượng, lịch sử upload gần đây.
  - `Users`: danh sách tài khoản từ SQLite.
  - `Files`: quét file trong `Code/Uploads`.
  - `Analytics`: thống kê theo trạng thái upload và loại file.
  - `Security`: thông tin auth, role control và lần đăng nhập gần nhất.
  - `Settings`: đường dẫn cấu hình/runtime đang dùng.

## Ghi chú demo

- Khi demo cùng một máy, Server để `0.0.0.0:8888`, Client gửi tới `127.0.0.1:8888`.
- Server xác minh SHA-256 sau khi nhận xong file.
- Server có nút `Mở` để xem file đã nhận.
- Client giữ style frontend mới, sidebar gồm `Upload Files`, `My Uploads` và `Hồ Sơ`.
- `My Uploads` đọc lịch sử upload thật từ `Code/config/client_upload_history.json`.
- Mặc định khi gửi lại cùng một file, client chọn `Bỏ qua nếu file đã có`: server chỉ xác minh checksum và trả về `Skipped`, không tạo bản sao mới.
- Nếu muốn gửi lại thật sự, chọn `Ghi đè file cũ` hoặc `Đổi tên tự động` trong màn hình Upload Files.
- Client có menu tốc độ demo, mặc định `5 MB/s`; nếu muốn test Pause/Resume/Stop rõ hơn thì chọn `2 MB/s`.
- File test có thể đặt trong `Extra/test-files/`.
- Thư mục `Code/Uploads/` là dữ liệu sinh ra khi chạy server, không cần đưa vào source code.
