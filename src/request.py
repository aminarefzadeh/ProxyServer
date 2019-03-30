class Request:
    def __init__(self, raw_packet=None):
        self.valid = True

        self.raw_data = raw_packet

        if raw_packet is None or len(raw_packet) == 0:
            self.valid = False
            self.method = ''
            self.uri = ''
            self.version = ''
            self.http_request_data = {}
            return

        http_lines = raw_packet.decode("utf-8", "ignore").split("\r\n")

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

        self.addr = self.http_request_data["Host"] + self.uri

        self.host_port = 80
        if ":" in self.http_request_data["Host"]:
            self.host_name = self.http_request_data["Host"].split(':')[0]
            self.host_port = int(self.http_request_data["Host"].split(':')[1])
        else:
            self.host_name = self.http_request_data["Host"]

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
        self.__dict__ = http_request.__dict__.copy()

        # self.method = http_request.method
        # self.uri = http_request.uri
        # self.body = http_request.body
        #

        self.http_request_data = http_request.http_request_data.copy()

        self.version = 'HTTP/1.0'
        self.http_request_data['Accept-Encoding'] = 'deflate'
        self.http_request_data['Connection'] = 'Close'
        self.http_request_data.pop('Proxy-Connection', None)

    def change_user_agent(self, user_agent):
        self.http_request_data['User-Agent'] = user_agent

    def clear_cache_header(self):
        self.http_request_data.pop('If-Modified-Since', None)
        self.http_request_data.pop('If-None-Match', None)
        self.http_request_data.pop('Cache-Control', None)

    def get_cache_header(self):
        ret = None
        if 'If-Modified-Since' in self.http_request_data:
            ret = ('If-Modified-Since', self.http_request_data['If-Modified-Since'])
        elif 'If-None-Match' in self.http_request_data:
            ret = ('If-None-Match', self.http_request_data['If-None-Match'])

        return ret
