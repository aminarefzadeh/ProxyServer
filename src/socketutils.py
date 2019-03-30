class SocketUtils:
    def __init__(self):
        return

    @staticmethod
    def recv_all(target_socket):
        message = b''
        try:
            while True:
                chunk = target_socket.recv(1)
                # print(message)
                if not chunk:
                    break
                message += chunk

        except Exception:
            return message
        return message
