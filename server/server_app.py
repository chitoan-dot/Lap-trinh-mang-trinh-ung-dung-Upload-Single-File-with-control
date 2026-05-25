from server.ui_server import ServerApp


def run_server():
    app = ServerApp()
    app.mainloop()


if __name__ == "__main__":
    run_server()
