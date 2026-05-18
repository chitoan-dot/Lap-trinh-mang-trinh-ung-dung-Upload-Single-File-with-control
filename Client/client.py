import customtkinter as ctk
from tkinter import filedialog, messagebox
import socket
import threading
import os
import struct
import time
import json
from PIL import Image

CONFIG_FILE = "client_config.json"

class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("File Upload Client - v2.0")
        self.geometry("600x550")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- State Variables ---
        self.file_path = ctk.StringVar()
        self.upload_state = "stopped"  # "stopped", "uploading", "paused"
        self.upload_thread = None
        self.client_socket = None

        # --- Load Icons (requires Pillow) ---
        self.start_icon = ctk.CTkImage(Image.open(self.get_asset_path("start.png")), size=(20, 20))
        self.pause_icon = ctk.CTkImage(Image.open(self.get_asset_path("pause.png")), size=(20, 20))
        self.resume_icon = ctk.CTkImage(Image.open(self.get_asset_path("resume.png")), size=(20, 20))
        self.stop_icon = ctk.CTkImage(Image.open(self.get_asset_path("stop.png")), size=(20, 20))
        self.browse_icon = ctk.CTkImage(Image.open(self.get_asset_path("browse.png")), size=(20, 20))

        # --- Tab View ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.tab_view.add("Upload")
        self.tab_view.add("Settings")
        
        self.setup_upload_tab()
        self.setup_settings_tab()
        
        # --- Main UI (Progress and Status) ---
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 5))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0.00% | 0.0 MB / 0.0 MB")
        self.progress_label.pack(padx=10, pady=2, anchor="w")
        
        self.speed_label = ctk.CTkLabel(self.progress_frame, text="Speed: 0.00 MB/s")
        self.speed_label.pack(padx=10, pady=2, anchor="w")

        self.status_label = ctk.CTkLabel(self, text="Welcome! Select a file and start the upload.", anchor="w")
        self.status_label.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Control Buttons ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.start_button = ctk.CTkButton(self.controls_frame, text="Start", image=self.start_icon, command=self.start_upload)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.pause_resume_button = ctk.CTkButton(self.controls_frame, text="Pause", image=self.pause_icon, command=self.pause_resume_upload, state=ctk.DISABLED)
        self.pause_resume_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(self.controls_frame, text="Stop", image=self.stop_icon, command=self.stop_upload, state=ctk.DISABLED, fg_color="#D32F2F", hover_color="#B71C1C")
        self.stop_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.load_config()
        self.update_ui_state()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_asset_path(self, asset_name):
        # A helper to find assets, especially when bundled with PyInstaller
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", asset_name)

    def setup_upload_tab(self):
        upload_tab = self.tab_view.tab("Upload")
        upload_tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(upload_tab, text="File to Upload:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.file_entry = ctk.CTkEntry(upload_tab, textvariable=self.file_path)
        self.file_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.browse_button = ctk.CTkButton(upload_tab, text="", image=self.browse_icon, command=self.browse_file, width=40)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkLabel(upload_tab, text="Server Subfolder:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.server_folder_entry = ctk.CTkEntry(upload_tab, placeholder_text="e.g., 'images' or 'docs/project_a' (optional)")
        self.server_folder_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    def setup_settings_tab(self):
        settings_tab = self.tab_view.tab("Settings")
        settings_tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_tab, text="Server IP Address:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.ip_entry = ctk.CTkEntry(settings_tab)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(settings_tab, text="Server Port:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.port_entry = ctk.CTkEntry(settings_tab)
        self.port_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.save_settings_button = ctk.CTkButton(settings_tab, text="Save Settings", command=self.save_config)
        self.save_settings_button.grid(row=2, column=1, padx=10, pady=20, sticky="e")

    def browse_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.file_path.set(file)
            self.status_label.configure(text=f"Selected: {os.path.basename(file)}")
            self.reset_progress()

    def reset_progress(self):
        self.progress_bar.set(0)
        self.progress_label.configure(text="0.00% | 0.0 MB / 0.0 MB")
        self.speed_label.configure(text="Speed: 0.00 MB/s")

    def update_ui_state(self):
        if self.upload_state == "stopped":
            self.start_button.configure(state=ctk.NORMAL)
            self.pause_resume_button.configure(state=ctk.DISABLED, text="Pause", image=self.pause_icon)
            self.stop_button.configure(state=ctk.DISABLED)
            self.browse_button.configure(state=ctk.NORMAL)
            self.file_entry.configure(state=ctk.NORMAL)
            self.tab_view.configure(state="normal")
        elif self.upload_state == "uploading":
            self.start_button.configure(state=ctk.DISABLED)
            self.pause_resume_button.configure(state=ctk.NORMAL, text="Pause", image=self.pause_icon)
            self.stop_button.configure(state=ctk.NORMAL)
            self.browse_button.configure(state=ctk.DISABLED)
            self.file_entry.configure(state=ctk.DISABLED)
            self.tab_view.configure(state="disabled")
        elif self.upload_state == "paused":
            self.pause_resume_button.configure(state=ctk.NORMAL, text="Resume", image=self.resume_icon)

    def start_upload(self):
        if not self.file_path.get() or not os.path.exists(self.file_path.get()):
            messagebox.showerror("Error", "Please select a valid file.", parent=self)
            return
        
        self.upload_state = "uploading"
        self.update_ui_state()
        self.upload_thread = threading.Thread(target=self.upload_file_thread, daemon=True)
        self.upload_thread.start()

    def pause_resume_upload(self):
        if self.upload_state == "uploading":
            self.upload_state = "paused"
            self.status_label.configure(text="Upload paused.")
        elif self.upload_state == "paused":
            self.upload_state = "uploading"
            self.status_label.configure(text="Resuming upload...")
        self.update_ui_state()

    def stop_upload(self):
        if self.upload_state in ["uploading", "paused"]:
            self.upload_state = "stopped"
            if self.client_socket:
                try:
                    self.client_socket.close()
                except Exception: pass
            self.status_label.configure(text="Upload stopped by user.")
            self.reset_progress()
            self.update_ui_state()

    def on_closing(self):
        self.stop_upload()
        self.save_config()
        self.destroy()

    def save_config(self):
        config = {
            "server_ip": self.ip_entry.get(),
            "server_port": self.port_entry.get()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            self.status_label.configure(text="Settings saved.")
        except Exception as e:
            self.status_label.configure(text=f"Error saving settings: {e}")

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.ip_entry.insert(0, config.get("server_ip", "127.0.0.1"))
                    self.port_entry.insert(0, config.get("server_port", "8888"))
            else:
                self.ip_entry.insert(0, "127.0.0.1")
                self.port_entry.insert(0, "8888")
        except Exception as e:
            self.status_label.configure(text=f"Error loading settings: {e}")

    def upload_file_thread(self):
        try:
            server_ip = self.ip_entry.get()
            server_port = int(self.port_entry.get())
            
            self.status_label.configure(text=f"Connecting to {server_ip}:{server_port}...")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.status_label.configure(text="Connected. Preparing to upload...")

            file_path = self.file_path.get()
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            target_dir = self.server_folder_entry.get()

            # Protocol: Command 'U' -> [DirNameLen][DirName][FileNameLen][FileName][FileSize]
            self.client_socket.sendall(b'U')
            
            dir_name_bytes = target_dir.encode()
            self.client_socket.sendall(struct.pack('!I', len(dir_name_bytes)))
            self.client_socket.sendall(dir_name_bytes)

            file_name_bytes = file_name.encode()
            self.client_socket.sendall(struct.pack('!I', len(file_name_bytes)))
            self.client_socket.sendall(file_name_bytes)

            self.client_socket.sendall(struct.pack('!Q', file_size))

            # Get offset from server for resume
            offset = struct.unpack('!Q', self.client_socket.recv(8))[0]
            self.status_label.configure(text=f"Server has {offset} bytes. Resuming...")

            with open(file_path, 'rb') as f:
                f.seek(offset)
                sent_bytes = offset
                
                last_update_time = time.time()
                bytes_in_last_second = 0

                while sent_bytes < file_size and self.upload_state != "stopped":
                    while self.upload_state == "paused":
                        time.sleep(0.1)
                        last_update_time = time.time() # Reset speed calc on resume
                        bytes_in_last_second = 0
                        if self.upload_state == "stopped": break
                    if self.upload_state == "stopped": break

                    data = f.read(65536)
                    if not data: break
                    
                    self.client_socket.sendall(data)
                    sent_bytes += len(data)
                    bytes_in_last_second += len(data)

                    # UI Update
                    current_time = time.time()
                    if (current_time - last_update_time) >= 0.5:
                        speed = bytes_in_last_second / (current_time - last_update_time) / (1024*1024)
                        self.speed_label.configure(text=f"Speed: {speed:.2f} MB/s")
                        bytes_in_last_second = 0
                        last_update_time = current_time

                    progress = sent_bytes / file_size
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"{progress:.2%} | {sent_bytes/1024/1024:.2f} MB / {file_size/1024/1024:.2f} MB")

            if self.upload_state != "stopped":
                self.status_label.configure(text="Upload complete!")
                self.upload_state = "stopped"

        except (ConnectionRefusedError, socket.gaierror):
            if self.upload_state != "stopped":
                messagebox.showerror("Connection Error", f"Could not connect to {server_ip}:{server_port}. Please check the server address and status.", parent=self)
                self.status_label.configure(text="Connection failed.")
        except Exception as e:
            if self.upload_state != "stopped":
                messagebox.showerror("Error", f"An error occurred: {e}", parent=self)
                self.status_label.configure(text="An error occurred.")
        finally:
            if self.client_socket:
                self.client_socket.close()
            self.upload_state = "stopped"
            self.update_ui_state()

if __name__ == "__main__":
    # Create assets folder and dummy icons if they don't exist
    if not os.path.exists("assets"):
        os.makedirs("assets")
    icon_names = ["start.png", "pause.png", "resume.png", "stop.png", "browse.png"]
    for name in icon_names:
        path = os.path.join("assets", name)
        if not os.path.exists(path):
            Image.new('RGBA', (24, 24), (0,0,0,0)).save(path)

    app = ClientApp()
    app.mainloop()
