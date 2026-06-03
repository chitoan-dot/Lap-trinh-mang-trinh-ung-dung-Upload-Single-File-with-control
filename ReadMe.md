# Upload Single File with Control

## Cau truc nop bai

- `Code/`: Source code cua chuong trinh.
- `DOCX/`: Bao cao Word (`.doc`, `.docx`).
- `Extra/`: Minh chung, hinh anh, file test upload, tai lieu bo sung.
- `PPTX/`: Slide thuyet trinh (`.ppt`, `.pptx`).

## Cach chay nhanh

Double-click:

```powershell
run_project.bat
```

File nay se mo 2 cua so:

- `Upload Server`: giao dien server PyQt.
- `Upload Client`: giao dien user PyQt.

Tren cua so Server bam `Bat dau`, sau do ben Client chon file va bam `Start`.

## Cach chay thu cong

Mo terminal tai thu muc project:

```powershell
pip install -r requirements.txt
cd Code
python main.py server
```

Mo terminal khac:

```powershell
cd Code
python main.py client
```

Cac che do khac:

```powershell
python main.py login
python main.py admin
```

`admin` mo Admin Panel cua frontend moi. Khi demo de tai upload, nen uu tien chay `server` va `client`.

## Tai khoan demo

- Admin mac dinh: `admin@uplower.local`
- Mat khau admin: `admin123`
- User moi co the tao tai man hinh `Dang ky`.
- Khi dang nhap phai chon dung vai tro. Tai khoan user khong the dang nhap vao Admin Panel.
- Admin Panel da doc du lieu that:
  - `Dashboard`: tong user, file, dung luong, lich su upload gan day.
  - `Users`: danh sach tai khoan tu SQLite.
  - `Files`: quet file trong `Code/Uploads`.
  - `Analytics`: thong ke theo trang thai upload va loai file.
  - `Security`: thong tin auth, role control va lan dang nhap gan nhat.
  - `Settings`: duong dan cau hinh/runtime dang dung.

## Ghi chu demo

- Khi demo cung mot may, Server de `0.0.0.0:8888`, Client gui toi `127.0.0.1:8888`.
- Server xac minh SHA-256 sau khi nhan xong file.
- Server co nut `Mo` de xem file da nhan.
- Client giu style frontend moi, sidebar gom `Upload Files`, `My Uploads` va `Ho So`.
- `My Uploads` doc lich su upload that tu `Code/config/client_upload_history.json`.
- Mac dinh khi gui lai cung mot file, client chon `Bo qua neu file da co`: server chi xac minh checksum va tra ve `Skipped`, khong tao ban sao moi.
- Neu muon gui lai that su, chon `Ghi de file cu` hoac `Doi ten tu dong` trong man hinh Upload Files.
- Client co menu toc do demo, mac dinh `5 MB/s`; neu muon test Pause/Resume/Stop ro hon thi chon `2 MB/s`.
- File test co the dat trong `Extra/test-files/`.
- Thu muc `Code/Uploads/` la du lieu sinh ra khi chay server, khong can dua vao source code.
