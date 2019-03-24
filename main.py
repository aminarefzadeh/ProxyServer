import socket
import sys
from threading import Thread


class Request:
    def __init__(self, raw_packet=None):
        self.valid = True

        if raw_packet is None:
            self.valid = False
            self.method = ''
            self.uri = ''
            self.version = ''
            self.http_request_data = {}
            return

        http_lines = raw_packet.decode("utf-8", "ignore").split("\r\n")

        while '' in http_lines:
            http_lines.remove('')

        if not len(http_lines):
            self.valid = False
            return

        self.method = http_lines[0].split()[0]
        self.uri = http_lines[0].split()[1]
        self.version = http_lines[0].split()[2]
        self.http_request_data = {}

        del http_lines[0]

        for item in http_lines:
            if ": " in item:
                parsed_line = item.split(": ")
                self.http_request_data[parsed_line[0]] = parsed_line[1]
            elif ":" in item:
                parsed_line = item.split(":")
                self.http_request_data[parsed_line[0]] = parsed_line[1]


class ClientRequest(Request):
    def __init__(self, sender_address, raw_packet):
        Request.__init__(self, raw_packet)
        http_lines = raw_packet.decode('utf-8', 'ignore').split("\r\n")
        while '' in http_lines:
            http_lines.remove('')

        self.sender_ip = sender_address[0]
        self.sender_port = sender_address[1]

    def __str__(self):
        return "\nfrom IP: " + str(self.sender_ip) + "\nfrom port:" + str(self.sender_port) + "\nmethod: " + str(
            self.method) + "\nuri:" + str(self.uri) + "\nversion:" + str(self.version) + "\noptions:" + str(
            self.http_request_data)


class ProxyRequest(Request):
    def __init__(self, http_request):
        Request.__init__(self)
        self.method = http_request.method
        self.uri = http_request.uri
        self.version = 'HTTP/1.0'

        self.http_request_data = http_request.http_request_data
        self.http_request_data['accept-encoding'] = 'deflate'
        self.http_request_data['Connection'] = 'Close'
        self.http_request_data.pop('Proxy-Connection', None)
        # print("HTTP options: \n" + str(self.http_request_data))

    def convert_to_message(self):
        if self.http_request_data["Host"] in self.uri:
            uri = self.uri[self.uri.find(self.http_request_data["Host"]) + len(self.http_request_data["Host"]):]
        else:
            uri = self.uri

        packet = self.method + ' ' + uri + ' ' + self.version + '\r\n'

        for key, value in self.http_request_data.items():
            packet += key + ': ' + value + '\r\n'

        packet += '\r\n'

        return packet


class Response:
    def __init__(self, raw_response=None):
        if raw_response is None:
            return

        http_lines = raw_response.decode('utf-8').split("\r\n")

        while '' in http_lines:
            http_lines.remove('')

        self.version = http_lines[0].split()[0]
        self.status_code = int(http_lines[0].split()[1])
        self.phrase = http_lines[0].split()[2]
        self.http_response_data = {}

        del http_lines[0]

        for item in http_lines:
            parsed_line = item.split(": ")
            self.http_response_data[parsed_line[0]] = parsed_line[1]


class RequestThread(Thread):
    def __init__(self, client_address, client_socket):
        Thread.__init__(self)
        self.client_address = client_address
        self.client_socket = client_socket
        print("New connection Thread added: ", client_address)

    def run(self):
        print(self.client_address)
        print("Connection from: ", self.client_address)

        self.client_socket.setblocking(0)

        while True:
            client_message = ''
            try:
                chunk = ''
                while True:
                    chunk = self.client_socket.recv(1)
                    if not chunk:
                        break
                    else:
                        client_message += chunk

            except Exception as exception:
                if client_message != '':
                    pass
                else:
                    return

            # client_message = self.client_socket.recv(1024)
            print("client message: \n" + client_message)
            print("client message len: \n" + str(len(client_message)))
            if len(client_message) == 0:
                self.client_socket.close()
                return

            http_request = ClientRequest(self.client_address, client_message)
            if not http_request.valid:
                continue

            proxy_port = 80
            proxy_request = ProxyRequest(http_request)
            if ":" in proxy_request.http_request_data["Host"]:
                hostname = proxy_request.http_request_data["Host"].split(':')[0]
                port = int(proxy_request.http_request_data["Host"].split(':')[1])
            else:
                hostname = proxy_request.http_request_data["Host"]

            print("Host IP fetching: %s" % hostname)
            host_ip = socket.gethostbyname(hostname)

            print("forwarding: " + host_ip + ":" + str(proxy_port))

            try:
                forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error as err:
                print("socket creation failed with error %s" % err)
                sys.exit()

            forward_socket.connect((host_ip, proxy_port))
            request = proxy_request.convert_to_message().encode()
            print("proxy request: \n" + request)
            forward_socket.send(request)
            forward_response = ''
            while True:
                chunk = forward_socket.recv(1)
                if not chunk:
                    break
                forward_response += chunk

            forward_socket.close()

            print("forward_response: \n" + forward_response + "\n\n")
            self.client_socket.send(forward_response)

        print("Thread finished")
        return


def main():
    server = socket.socket()
    print("Socket successfully created")
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = int(sys.argv[1])

    server.bind(('', port))
    print("socket binded to %s" % port)

    while True:
        server.listen(10)
        print("socket is listening")
        client_socket, client_address = server.accept()

        connection_thread = RequestThread(client_address, client_socket)
        connection_thread.start()


if __name__ == '__main__':
    main()
