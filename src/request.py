class Request:
    def __init__(self, raw_packet=None):
        self.valid = True

        if raw_packet is None or len(raw_packet) == 0:
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

