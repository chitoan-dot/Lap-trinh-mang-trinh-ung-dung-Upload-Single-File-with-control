import customtkinter as ctk
import socket
import threading
import os
import struct
from datetime import datetime
import tkinter as tk

class ServerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("File Upload Server - v2.0")
        self.geometry("700x500")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.main_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.main_frame, text="IP Address:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(20, 5), pady=10)
        self.ip_entry = ctk.CTkEntry(self.main_frame, placeholder_text="0.0.0.0")
        self.ip_entry.insert(0, "0.0.0.0")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        ctk.CTkLabel(self.main_frame, text="Port:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=(10, 5), pady=10)
        self.port_entry = ctk.CTkEntry(self.main_frame, placeholder_text="8888", width=80)
        self.port_entry.insert(0, "8888")
        self.port_entry.grid(row=0, column=3, padx=(0, 20), pady=10)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Server is Stopped", text_color="orange", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=1, column=0, columnspan=4, padx=20, pady=(5, 10))

        # --- Tab View for Logs and Clients ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.tab_view.add("Logs")
        self.tab_view.add("Connected Clients")

        self.log_area = ctk.CTkTextbox(self.tab_view.tab("Logs"))
        self.log_area.pack(expand=True, fill="both", padx=5, pady=5)
        self.log_area.configure(state="disabled")

        self.clients_list = tk.Listbox(self.tab_view.tab("Connected Clients"), bg="#2B2B2B", fg="white", selectbackground="#1F6AA5", relief="flat", borderwidth=0)
        self.clients_list.pack(expand=True, fill="both", padx=5, pady=5)

        # --- Control Buttons ---
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_frame.grid(row=2, column=0, sticky="ew")
        self.bottom_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_button = ctk.CTkButton(self.bottom_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.stop_button = ctk.CTkButton(self.bottom_frame, text="Stop Server", command=self.stop_server, state=ctk.DISABLED, fg_color="#D32F2F", hover_color="#B71C1C")
        self.stop_button.grid(row=0, column=1, padx=20, pady=10, sticky="ew")

        self.server_socket = None
        self.listen_thread = None
        self.running = False
        self.clients = {} # To store client sockets and addresses

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        def _insert():
            self.log_area.configure(state="normal")
            self.log_area.insert("end", log_message)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
        self.after(0, _insert)

    def update_clients_list(self):
        def _update():
            self.clients_list.delete(0, tk.END)
            for addr, _ in self.clients.items():
                self.clients_list.insert(tk.END, f"{addr[0]}:{addr[1]}")
        self.after(0, _update)

    def start_server(self):
        ip = self.ip_entry.get()
        port_str = self.port_entry.get()
        if not port_str.isdigit():
            self.log("Invalid port number.", "ERROR")
            return
        port = int(port_str)

        self.running = True
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((ip, port))
            self.server_socket.listen(5)
            
            self.listen_thread = threading.Thread(target=self.listen_for_clients)
            self.listen_thread.daemon = True
            self.listen_thread.start()

            self.status_label.configure(text=f"Server is running on {ip}:{port}", text_color="green")
            self.log(f"Server started on {ip}:{port}")
            self.start_button.configure(state=ctk.DISABLED)
            self.stop_button.configure(state=ctk.NORMAL)
            self.ip_entry.configure(state="disabled")
            self.port_entry.configure(state="disabled")
        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            self.running = False

    def stop_server(self):
        self.running = False
        # Close all client connections
        for addr, client_socket in list(self.clients.items()):
            client_socket.close()
            self.log(f"Closed connection to {addr}")
        self.clients.clear()
        self.update_clients_list()

        if self.server_socket:
            try:
                # Dummy connection to unblock accept()
                dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dummy_socket.settimeout(1)
                dummy_socket.connect((self.ip_entry.get(), int(self.port_entry.get())))
                dummy_socket.close()
            except Exception:
                pass
            finally:
                self.server_socket.close()
                self.server_socket = None

        self.status_label.configure(text="Server is Stopped", text_color="orange")
        self.log("Server stopped.")
        self.start_button.configure(state=ctk.NORMAL)
        self.stop_button.configure(state=ctk.DISABLED)
        self.ip_entry.configure(state="normal")
        self.port_entry.configure(state="normal")

    def listen_for_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                if not self.running:
                    break
                
                self.clients[addr] = client_socket
                self.log(f"Accepted connection from {addr}")
                self.update_clients_list()

                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_handler.daemon = True
                client_handler.start()
            except OSError:
                if self.running:
                    self.log("Error accepting connections.", "ERROR")
                break

    def handle_client(self, client_socket, addr):
        try:
            # Protocol: [Command: 1 byte]
            # Command 'U': Upload
            # 'U' -> [DirNameLen: 4 bytes][DirName: N bytes][FileNameLen: 4 bytes][FileName: N bytes][FileSize: 8 bytes][FileData: N bytes]
            
            command_byte = client_socket.recv(1)
            if not command_byte:
                raise ConnectionAbruptlyClosed("Client closed connection before sending command.")

            command = command_byte.decode()

            if command == 'U':
                # Read target directory name length and name
                dir_name_len = struct.unpack('!I', client_socket.recv(4))[0]
                target_dir = client_socket.recv(dir_name_len).decode() if dir_name_len > 0 else ""

                # Read file name length and name
                file_name_len = struct.unpack('!I', client_socket.recv(4))[0]
                file_name = client_socket.recv(file_name_len).decode()

                # Read file size
                file_size = struct.unpack('!Q', client_socket.recv(8))[0]

                self.log(f"Client {addr} wants to upload '{file_name}' ({file_size} bytes) to '{target_dir}/'")

                # Create directory structure
                base_upload_dir = 'Uploads'
                final_dir = os.path.join(base_upload_dir, target_dir)
                os.makedirs(final_dir, exist_ok=True)
                file_path = os.path.join(final_dir, file_name)

                # Check existing file size for resume
                offset = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                client_socket.sendall(struct.pack('!Q', offset))

                if offset >= file_size:
                    self.log(f"File '{file_name}' already fully uploaded. Skipping.", "WARN")
                else:
                    self.log(f"Resuming upload for '{file_name}' from {offset} bytes.")
                    with open(file_path, 'ab') as f:
                        f.seek(offset)
                        received_bytes = offset
                        while received_bytes < file_size:
                            data = client_socket.recv(65536)
                            if not data:
                                break
                            f.write(data)
                            received_bytes += len(data)
                    self.log(f"Finished receiving '{file_name}' from {addr}.")
            else:
                self.log(f"Unknown command '{command}' from {addr}", "WARN")

        except ConnectionAbruptlyClosed as e:
            self.log(f"Client {addr} disconnected abruptly: {e}", "WARN")
        except Exception as e:
            self.log(f"Error handling client {addr}: {e}", "ERROR")
        finally:
            client_socket.close()
            if addr in self.clients:
                del self.clients[addr]
            self.log(f"Connection with {addr} closed.")
            self.update_clients_list()

    def on_closing(self):
        self.stop_server()
        self.destroy()

class ConnectionAbruptlyClosed(Exception):
    pass

if __name__ == "__main__":
    app = ServerApp()
    app.mainloop()
