from threading import Thread
import socket

from src.restricts import Restricts
from src.logger import Logger
from src.request import ProxyRequest,ClientRequest
from src.response import ProxyResponse
from src.cache import LRUCache,CacheHandler
from src.socketutils import SocketUtils

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
        LRUCache.set_capacity(self.config.cache_size)
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

        cache_handler = CacheHandler(self.config)

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

            proxy_response = cache_handler.parseRequest(proxy_request)

            if proxy_response is None:
                Logger.log_message("server response is not valid")
                # self.client_socket.send(
                #     ProxyServerThread.error_page(self.config, 404, "Not Found").encode('utf-8', 'ignore'))
                break

            Logger.log_packet(str(proxy_response), "Server Response")

            if 'text/html' in proxy_response.http_request_data.get('Content-Type', ''):
                proxy_response.inject(config=self.config)
                self.client_socket.send(proxy_response.convert_to_message().encode('utf-8', 'ignore'))
            else:
                self.client_socket.send(proxy_response.raw_data)
        return


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



