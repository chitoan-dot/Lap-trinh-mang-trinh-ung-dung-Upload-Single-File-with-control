# UPLOWER - Upload Single File with Control

- Project name: UPLOWER
- Project code: Upload Single File with Control

Ứng dụng desktop mô hình Client - Server phục vụ upload một tệp với khả năng điều khiển quá trình truyền. Dự án hỗ trợ chia tệp thành nhiều chunk, truyền đồng thời qua nhiều luồng và xác minh tính toàn vẹn bằng SHA-256.

## Chức năng chính

### User / Client

- Đăng ký, đăng nhập và khôi phục mật khẩu.
- Chọn hoặc kéo thả một tệp để upload.
- Điều khiển bằng các nút `Start`, `Pause`, `Resume` và `Stop`.
- Chọn kích thước chunk: `1 MB`, `5 MB` hoặc `10 MB`.
- Chọn số luồng truyền đồng thời: `1`, `2` hoặc `4`.
- Chọn giới hạn tốc độ để thuận tiện kiểm thử.
- Theo dõi tiến trình tổng, tốc độ và trạng thái từng chunk.
- Xem lịch sử upload và hồ sơ người dùng.

### Admin / Server

- Khởi động và dừng máy chủ nhận tệp.
- Theo dõi kết nối, tiến trình nhận và nhật ký hoạt động.
- Quản lý tài khoản, file đã nhận và lịch sử upload.
- Xem số liệu tổng quan và phân tích.
- Mở file hoặc thư mục lưu trữ trực tiếp từ giao diện.
- Xác minh SHA-256 sau khi ghép xong các chunk.

## Yêu cầu môi trường

- Windows 10/11.
- Python 3.10 trở lên và đã thêm vào biến môi trường `PATH`.
- Thư viện trong [Code/requirements.txt](Code/requirements.txt).

Cài thư viện:

```powershell
python -m pip install -r Code/requirements.txt
```

## Chạy thủ công

Mở terminal tại thư mục gốc của dự án.

### Màn hình đăng nhập

```powershell
cd Code
python main.py login
```

### Server

```powershell
cd Code
python main.py server
```

### Client

```powershell
cd Code
python main.py client
```

### Admin Panel

```powershell
cd Code
python main.py admin
```

## Chạy 2 máy cùng Wi-Fi

Máy Server là nơi giữ database tài khoản chính tại `Code/Database/users.db`.

### Máy A - Server

1. Kết nối cùng Wi-Fi với máy Client.
2. Chạy Server:

```powershell
cd Code
python main.py server
```

3. Bấm `Bắt đầu` để Server lắng nghe cổng `8888`.
4. Lấy địa chỉ IPv4 LAN của máy Server:

```powershell
ipconfig
```

Tìm dòng `IPv4 Address`, ví dụ:

```text
192.168.1.10
```

Nếu Windows Firewall hỏi quyền truy cập mạng, chọn `Allow access`.

### Máy B - Client

1. Kết nối cùng Wi-Fi với máy Server.
2. Mở `Code/config/client_config.json`.
3. Sửa `server_ip` thành IPv4 của máy Server:

```json
{
  "server_ip": "192.168.1.10",
  "server_port": "8888",
  "server_folder": "",
  "duplicate_policy": "Tiep tuc file dang do",
  "speed_limit": "5 MB/s"
}
```

4. Chạy Client/Login:

```powershell
cd Code
python main.py login
```

Tài khoản User đăng ký, đăng nhập và đặt lại mật khẩu sẽ được gửi tới Server để dùng chung database. Tài khoản Admin vẫn dùng database local trên máy Server để có thể đăng nhập và bật Server.

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
| --- | --- | --- |
| Admin | `admin@uplower.local` | `admin123` |

User mới có thể được tạo tại màn hình `Đăng ký`. Khi đăng nhập, phải chọn đúng vai trò; tài khoản User không thể truy cập Admin Panel.

Chức năng `Quên mật khẩu` tạo mã xác minh 6 chữ số có hiệu lực trong 5 phút. Do dự án chưa tích hợp dịch vụ email, mã demo được hiển thị trực tiếp trong ứng dụng.

## Quy trình demo đề xuất

1. Mở hai terminal tại thư mục dự án.
2. Chạy `cd Code` rồi `python main.py login` trong cả hai terminal.
3. Ở cửa sổ thứ nhất, chọn `Admin` và đăng nhập bằng tài khoản demo.
4. Mở mục `Server`, sau đó bấm `Bắt đầu`.
5. Ở cửa sổ thứ hai, đăng nhập hoặc đăng ký tài khoản User.
6. Mở `Upload file` và kiểm tra trạng thái kết nối Server.
7. Chọn một file, cấu hình `Chunk Size`, `Threads` và tốc độ.
8. Bấm `Start`; trong lúc truyền, lần lượt demo `Pause`, `Resume` và `Stop`.
9. Upload lại file nếu đã Stop, sau đó chờ hoàn tất và kiểm tra checksum.
10. Quay lại Admin để xem file, lịch sử, tài khoản và số liệu phân tích.

## Multi-chunk upload hoạt động thế nào?

Client chia một file thành nhiều phần nhỏ gọi là chunk. Ví dụ, file `850 MB` với chunk `5 MB` sẽ có khoảng `170` chunk.

Tùy chọn `Threads` quyết định số worker/socket gửi song song:

- `1`: gửi từng chunk tuần tự.
- `2`: tối đa hai chunk được gửi đồng thời.
- `4`: tối đa bốn chunk được gửi đồng thời.

Mỗi chunk vẫn được stream thành các gói nhỏ `64 KB`, nhờ đó chương trình không cần nạp toàn bộ file vào RAM. Server lưu các phần tạm, ghép chúng theo đúng thứ tự rồi kiểm tra SHA-256 của file hoàn chỉnh.

## Địa chỉ và dữ liệu

- Server lắng nghe mặc định tại `0.0.0.0:8888`.
- Client kết nối tới địa chỉ trong `Code/config/client_config.json`.
- File nhận được lưu trong `Code/Uploads/`.
- Lịch sử phía Client được lưu tại `Code/config/client_upload_history.json`.
- Cơ sở dữ liệu tài khoản chính nằm tại `Code/Database/users.db` trên máy Server.
- Khi trùng tên, Server tự đổi tên file mới để tránh ghi đè dữ liệu cũ.

## Cấu trúc dự án

```text
Code/           Mã nguồn ứng dụng
  admin/        Giao diện và chức năng quản trị
  auth/         Đăng nhập, đăng ký và khôi phục mật khẩu
  client/       Giao diện và xử lý upload phía Client
  common/       Hằng số và giao thức dùng chung
  config/       Cấu hình Client và Server
  Database/     SQLite và lớp truy cập dữ liệu
  layout/       Theme và style giao diện
  profile/      Giao diện hồ sơ người dùng
  server/       Socket server và xử lý nhận file
  requirements.txt
  Uploads/      File được Server nhận khi chạy
DOCX/           Báo cáo Word
Extra/          Tài liệu và file kiểm thử bổ sung
PPTX/           Slide thuyết trình
ReadMe.md       Tên dự án, mã dự án và hướng dẫn chạy
```

## Lưu ý khi kiểm thử

- Dùng file đủ lớn và chọn tốc độ `2 MB/s` nếu cần quan sát rõ `Pause`, `Resume` và `Stop`.
- Nếu Client chưa kết nối, kiểm tra Server đã được bấm `Bắt đầu` và cổng `8888` chưa bị chương trình khác sử dụng.
- Không tắt Server khi đang ghép chunk hoặc xác minh checksum.
- `Code/Uploads/` là dữ liệu phát sinh trong quá trình chạy, không phải mã nguồn bắt buộc khi nộp dự án.
