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

Sau do tren cua so Server bam `Bat dau`, roi dung Client de gui file.

## Cach chay thu cong

Mo terminal tai thu muc project, sau do chay:

```powershell
cd Code
pip install customtkinter pillow tkinterdnd2
python main.py server
```

Mo them terminal khac:

```powershell
cd Code
python main.py client
```

Nen chay server truoc, sau do moi chay client.

## Ghi chu demo

- Khi demo cung mot may, Server co the de `0.0.0.0:8888`, Client nen ket noi `127.0.0.1:8888`.
- Client co nut `Kiem tra ket noi` de xac nhan server da san sang truoc khi upload.
- Toc do demo mac dinh la `5 MB/s`; neu muon test Pause/Resume/Stop ro hon thi chon `1 MB/s`.
- Server xac minh SHA-256 sau khi nhan xong file de tranh file loi khi truyen.
- File dung de test upload co the dat trong `Extra/test-files/`.
- Thu muc `Uploads/` la du lieu sinh ra khi chay server, khong can dua vao source code.
