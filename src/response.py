from bs4 import BeautifulSoup

class Response:
    def __init__(self, raw_packet=None):
        self.valid = True

        self.raw_data = raw_packet

        if raw_packet is None or len(raw_packet) == 0:
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
        self.message = http_lines[0][http_lines[0].find(str(self.status)) + len(str(self.status)) + 1:]

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
    def __init__(self, raw_input):
        Response.__init__(self, raw_input)

    def inject(self, config):
        if not config.must_inject:
            return
        if not self.valid:
            return
        if self.status != 200:
            return
        if 'text/html' not in self.http_request_data.get('Content-Type', ''):
            return

        soup = BeautifulSoup(self.body, 'html.parser')
        injection_element = soup.new_tag('p', id='ProxyInjection')
        injection_element.attrs['style'] = 'background-color:brown; height:40px; width:100%; position:fixed; ' \
                                           'top:0px; left:0px; margin:0px; padding: 15px 0 0 0;' \
                                           'z-index: 1060; text-align: center; color: white'
        injection_element.insert(0, config.injection_body)
        if soup.body:
            soup.body.insert(0, injection_element)
            self.body = soup.prettify()
