from threading import Thread
import socket

from src.restricts import Restricts
from src.logger import Logger
from src.request import ProxyRequest,ClientRequest
from src.response import ProxyResponse

class Server:
    def __init__(self, config):
        self.config = config
        self.host = config.host
        self.port = config.port

    def start_server(self):
        server_socket = socket.socket()
        Logger.log_message("Server socket is listening....")
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = self.port

        server_socket.bind((self.host, self.port))
        Logger.log_message("Server socket bind to port %s" % port)
        Logger.log_message("Server socket listening for incoming connections...")
        while True:
            server_socket.listen(10)
            client_socket, client_address = server_socket.accept()

            connection_thread = ProxyServerThread(client_address, client_socket, self.config)
            connection_thread.start()


class ProxyServerThread(Thread):
    def __init__(self, client_address, client_socket, config):
        Thread.__init__(self)
        self.config = config
        self.client_address = client_address
        self.client_socket = client_socket
        # print("New connection Thread added: ", client_address)

    def run(self):
        Logger.log_message("Connection from address %s" % str(self.client_address))
        # print("Connection from: ", self.client_address)

        self.client_socket.setblocking(0)

        while True:
            client_message = SocketUtils.recv_all(self.client_socket)
            if len(client_message) == 0:
                self.client_socket.close()
                break

            http_request = ClientRequest(self.client_address, client_message)
            if not http_request.valid:
                continue

            if http_request.method == "CONNECT":
                Logger.log_message("TLS request ignored")
                self.client_socket.send(
                    ProxyServerThread.error_page(self.config, 403, "Forbidden").encode('utf-8', 'ignore'))
                continue

            Logger.log_packet(str(http_request), "Client Request")

            restrictor = Restricts(self.config)
            restriction_rule = restrictor.check_access(http_request)
            if restriction_rule is not None:
                restrictor.send_disallow_response(self.client_socket, http_request, restriction_rule.notify)
                # return or break ???
                return

            proxy_request = ProxyRequest(http_request)

            if self.config.get_user_agent() is not None:
                proxy_request.change_user_agent(self.config.get_user_agent())

            forward_socket = ProxyServerThread.establish_forwarding_socket(http_request)
            if forward_socket is None:
                break

            forward_socket.send(proxy_request.convert_to_message().encode('ascii', 'ignore'))
            forward_socket.settimeout(2)
            forward_response = SocketUtils.recv_all(forward_socket)
            forward_socket.close()

            proxy_response = ProxyResponse(forward_response)
            Logger.log_packet(str(proxy_response), "Server Response")

            if 'text/html' in proxy_response.http_request_data.get('Content-Type', ''):
                proxy_response.inject(config=self.config)
                self.client_socket.send(proxy_response.convert_to_message().encode('utf-8', 'ignore'))
            else:
                self.client_socket.send(proxy_response.raw_data)
        return

    @staticmethod
    def establish_forwarding_socket(proxy_request):
        proxy_port = 80
        if ":" in proxy_request.http_request_data["Host"]:
            hostname = proxy_request.http_request_data["Host"].split(':')[0]
            proxy_port = int(proxy_request.http_request_data["Host"].split(':')[1])
        else:
            hostname = proxy_request.http_request_data["Host"]

        host_ip = socket.gethostbyname(hostname)

        try:
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            return None

        forward_socket.settimeout(1)
        try:
            forward_socket.connect((host_ip, proxy_port))

        except Exception:
            forward_socket.close()
            return None

        return forward_socket

    @staticmethod
    def error_page(config, status, message):
        http_message = "<!DOCTYPE html>" \
                       "<html>" \
                       "<head><title>Forbidden</title></head>" \
                       "<body>" \
                       "<h1> " + str(status) + " " + str(message) + " </h1>" \
                                                                    "</body>" \
                                                                    "</html>"

        message = "HTTP/1.1 " + str(status) + " " + str(message) + "\r\n"
        message += "Server: " + config.get_server_name() + "\r\n"
        message += "Content-Type: text/html; charset=utf-8"
        message += "Content-Length: " + str(len(http_message)) + "\r\n"
        message += "Connection: Closed \r\n"
        message += "\r\n"
        message += http_message
        return message


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
