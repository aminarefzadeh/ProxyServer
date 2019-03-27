from threading import Thread
import socket
import sys

from src.restricts import Restricts
from src.logger import Logger


class Request:
    def __init__(self, raw_packet=None):
        self.valid = True

        if raw_packet is None or raw_packet is '':
            self.valid = False
            self.method = ''
            self.uri = ''
            self.version = ''
            self.http_request_data = {}
            return

        http_lines = raw_packet.decode("utf-8", "ignore").split("\r\n")

        # self.body = raw_packet[raw_packet.find("\r\n\r\n".encode("ascii")) + 4:]

        # while '' in http_lines:
        #     http_lines.remove('')

        if not len(http_lines):
            self.valid = False
            return

        self.method = http_lines[0].split()[0]
        self.uri = http_lines[0].split()[1]
        self.version = http_lines[0].split()[2]
        self.http_request_data = {}

        del http_lines[0]

        index = 0
        for index in range(0,len(http_lines)):
            item = http_lines[index]
            if item == '' :
                break
            if ": " in item:
                parsed_line = item.split(": ")
                self.http_request_data[parsed_line[0]] = parsed_line[1]
            elif ":" in item:
                parsed_line = item.split(":")
                self.http_request_data[parsed_line[0]] = parsed_line[1]

        self.body=''
        index += 1

        while index < len(http_lines):
            self.body += http_lines[index]
            self.body += "\r\n"
            index += 1

        if self.http_request_data["Host"] in self.uri:
            self.uri = self.uri[self.uri.find(self.http_request_data["Host"]) + len(self.http_request_data["Host"]):]


    def convert_to_message(self):


        packet = self.method + ' ' + self.uri + ' ' + self.version + '\r\n'

        for key, value in self.http_request_data.items():
            packet += key + ': ' + value + '\r\n'

        packet += '\r\n'

        packet += self.body

        return packet

    def __str__(self):
        return "\nmethod: " + str(self.method) + "\nuri:" + str(self.uri) + \
               "\nversion:" + str(self.version) + "\noptions:" + str(self.http_request_data)


class ClientRequest(Request):
    def __init__(self, sender_address, raw_packet):
        Request.__init__(self, raw_packet)
        # http_lines = raw_packet.decode('utf-8', 'ignore').split("\r\n")
        # while '' in http_lines:
        #     http_lines.remove('')

        self.sender_ip = sender_address[0]
        self.sender_port = sender_address[1]

    def __str__(self):
        return "\nfrom IP: " + str(self.sender_ip) + "\nfrom port:" + str(self.sender_port) + \
               "\nmethod: " + str(self.method) + "\nuri:" + str(self.uri) + \
               "\nversion:" + str(self.version) + "\noptions:" + str(self.http_request_data)


class ProxyRequest(Request):
    def __init__(self, http_request):
        Request.__init__(self)
        self.method = http_request.method
        self.uri = http_request.uri
        self.version = 'HTTP/1.0'

        self.http_request_data = http_request.http_request_data
        self.http_request_data['Accept-Encoding'] = 'deflate'
        self.http_request_data['Connection'] = 'Close'
        self.http_request_data.pop('Proxy-Connection', None)

        self.body = http_request.body

    def change_user_agent(self, user_agent):
        self.http_request_data['User-Agent'] = user_agent



from bs4 import BeautifulSoup

class Response():
    def __init__(self, raw_packet=None):
        self.valid = True

        if raw_packet is None or raw_packet is '':
            self.valid = False
            self.message = ''
            self.status = 400
            self.version = ''
            self.http_request_data = {}
            self.body = ''
            return

        http_lines = raw_packet.decode("utf-8", "ignore").split("\r\n")

        # self.body = raw_packet[raw_packet.find("\r\n\r\n".encode("ascii"))+4:]

        if not len(http_lines):
            self.valid = False
            return

        self.version = http_lines[0].split()[0]
        self.status = int(http_lines[0].split()[1])
        self.message = http_lines[0][http_lines[0].find(str(self.status))+len(str(self.status))+1:]

        self.http_request_data = {}

        del http_lines[0]

        index = 0
        for index in range(0, len(http_lines)):
            item = http_lines[index]
            if item == '':
                break
            if ": " in item:
                parsed_line = item.split(": ")
                self.http_request_data[parsed_line[0]] = parsed_line[1]
            elif ":" in item:
                parsed_line = item.split(":")
                self.http_request_data[parsed_line[0]] = parsed_line[1]

        self.body = ''
        index += 1

        while index < len(http_lines):
            self.body += http_lines[index]
            self.body += "\r\n"
            index += 1

    def convert_to_message(self):

        # self.http_request_data['Content-Length'] = str(len(self.body))
        if 'Content-Length' in self.http_request_data:
            self.http_request_data.pop('Content-Length')

        packet = self.version + ' ' + str(self.status) + ' ' + self.message + '\r\n'

        for key, value in self.http_request_data.items():
            packet += key + ': ' + value + '\r\n'

        packet += '\r\n'

        packet += self.body

        return packet

    def __str__(self):
        return "\nversion: " + str(self.version) + "\nstatus:" + str(self.status) + \
               "\nmessage:" + str(self.message) + "\noptions:" + str(self.http_request_data)


class ProxyResponse(Response):
    def __init__(self,raw_input):
        Response.__init__(self,raw_input)

    def inject(self,config):
        if not config.must_inject:
            return
        if not self.valid:
            return
        if self.status != 200:
            return
        if not 'text/html' in self.http_request_data.get('Content-Type','')  :
            return

        soup = BeautifulSoup(self.body,'html.parser')
        injection_element = soup.new_tag('p',id='ProxyInjection')
        injection_element.attrs['style'] = 'background-color:brown; height:40px; width:100%; position:absolute; top:0px; left:0px; margin:0px; z-index: 1060; text-align: center;'
        injection_element.insert(0,config.injection_body)
        if soup.body:
            soup.body.insert(0,injection_element)
            self.body = soup.prettify()



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
                self.client_socket.send(ProxyServerThread.error_page(self.config,403,"Forbidden").encode('utf-8','ignore'))
                continue


            Logger.log_packet(str(http_request), "Client Request")

            restrictor = Restricts(self.config)
            restriction_rule = restrictor.check_access(http_request)

            if not (restriction_rule is None):
                # print("restricted")
                restrictor.send_disallow_response(self.client_socket, http_request)
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


            if 'text/html' in proxy_response.http_request_data.get('Content-Type',''):
                proxy_response.inject(config=self.config)
                self.client_socket.send(proxy_response.convert_to_message().encode('utf-8','ignore'))
            else:
                self.client_socket.send(forward_response)
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
        except socket.error as err:
            return None

        forward_socket.settimeout(1)
        try:
            forward_socket.connect((host_ip, proxy_port))

        except Exception:
            forward_socket.close()
            return None

        return forward_socket

    @staticmethod
    def error_page(config,status,message):
        http_message = "<!DOCTYPE html>" \
                       "<html>" \
                       "<head><title>Forbidden</title></head>" \
                       "<body>" \
                       "<h1> "+str(status) + " " + str(message) +" </h1>" \
                       "</body>" \
                       "</html>"

        message = "HTTP/1.1 "+ str(status) + " " + str(message) + "\r\n"
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

        except Exception as err:
            return message
        return message
