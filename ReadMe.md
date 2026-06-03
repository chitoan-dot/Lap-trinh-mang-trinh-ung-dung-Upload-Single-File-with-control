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

`admin` mở trực tiếp Admin Panel. Khi demo chuẩn, nên dùng `login` ở cả 2 terminal để đi đúng luồng đăng nhập và phân quyền.

## Cách demo đúng luồng desktop app

Khi demo chuẩn, nên mở **2 terminal** để chạy 2 cửa sổ đăng nhập riêng biệt.
Cả 2 terminal đều chạy màn hình login, sau đó một bên đăng nhập Admin và một bên đăng nhập User.

Terminal 1:

```powershell
cd Code
python main.py login
```

Terminal 2:

```powershell
cd Code
python main.py login
```

Luồng demo gợi ý:

1. Ở Terminal 1, chọn vai trò `Admin` và đăng nhập bằng tài khoản mặc định.
2. Trong Admin Panel, giới thiệu nhanh các phần: Tổng quan, Tài khoản, File, Phân tích, Bảo mật, Server, Hồ sơ, Cài đặt.
3. Vào tab `Server` trong Admin Panel và bấm `Bắt đầu` để server lắng nghe socket.
4. Ở Terminal 2, đăng nhập hoặc đăng ký tài khoản `User`.
5. User vào tab `Upload file`.
6. Kiểm tra trạng thái Server bên User. Nếu Admin đã bật Server, User sẽ thấy `Server: Đã kết nối 127.0.0.1:8888`.
7. User chọn file hoặc kéo thả file vào vùng upload.
8. Chọn chế độ xử lý file trùng, ví dụ `Bỏ qua nếu file đã có`, rồi bấm `Start`.
9. Trong lúc upload có thể demo các nút `Pause`, `Resume`, `Stop`.
10. Sau khi upload xong, quay lại Admin:
    - Tab `Server`: xem log nhận file.
    - Tab `File`: xem file đã nhận, người upload và bấm `Mở` để mở file.
    - Tab `Tài khoản`: bấm `Xem` để xem chi tiết user và lịch sử upload của user đó.
    - Tab `Phân tích`: xem thống kê theo trạng thái upload và loại file.

Giải thích khi demo: đây là mô hình client-server nên Admin/Server và User/Client cần chạy song song.
Admin là bên quản lý và bật Server, còn User là bên gửi file. `run_project.bat` chỉ là chế độ mở nhanh Server + Client để kiểm thử chức năng upload, không phải luồng demo đầy đủ.

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
