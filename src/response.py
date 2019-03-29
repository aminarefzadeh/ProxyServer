from bs4 import BeautifulSoup

class Response:
    def __init__(self, raw_packet=None):
        self.valid = True
        self.message = ''
        self.status = 400
        self.version = 'HTTP/1.1'
        self.http_request_data = {}
        self.body = ''


        self.raw_data = raw_packet

        if raw_packet is None or len(raw_packet) == 0:
            self.valid = False
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

        self.cache = CacheController(self.http_request_data,self.status)

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
    def __init__(self, raw_input=None):
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



import datetime

class CacheController():

    time_format = '%a, %d %b %Y %H:%M:%S GMT'
    def __init__(self,response_header,status):
        # self.expire_date
        # self.cache_status
        # self.date
        # self.modify_date
        # self.init_time

        self.refresh_time = datetime.datetime.now()

        self.cache_id = ''
        self.cache_request_header = ('','')

        if 'Last-Modified' in response_header :
            self.cache_id = ('Last-Modified',response_header.get('Last-Modified'))
            self.cache_request_header = ('If-Modified-Since',self.cache_id)

        elif 'Etag' in response_header:
            self.cache_id = ('Etag',response_header.get('Etag'))
            self.cache_request_header = ('If-None-Match',self.cache_id)
        else:
            self.cachable = False



        cache_header = response_header.get('Cache-Control','').lower()
        if cache_header=='':
            cache_header = response_header.get('Pragma','').lower()

        if 'no-cache' in cache_header or status != 200 :
            self.cachable = False


        if 'max-age' in cache_header:
            cache_header = cache_header[cache_header.find('max-age')+len('max-age'):]
            cache_header = cache_header[cache_header.find('=')+1:]
            datetime.timedelta()
            self.age = datetime.timedelta(seconds=int(cache_header.split()[0]))

        elif 'Date' in response_header and 'Expires' in response_header:
            self.age = datetime.datetime.strptime(response_header.get('Expires'))-datetime.datetime.strptime(response_header.get('Date'))

        else:
            self.age = datetime.timedelta(0)

    def __init__(self):
        self.refresh_time = datetime.datetime.now()
        self.cache_id = ''
        self.cache_request_header = ('', '')
        self.cachable = False
        self.age = datetime.timedelta(0)

    def is_expire(self):
        now = datetime.datetime.now()
        return self.refresh_time + self.age <= now

    def get_cache_request_header(self):
        return self.cache_request_header

    def update_cache(self,new_cache):
        self.age = new_cache.age
        self.refresh_time = new_cache.refresh_time

    def is_cachable(self):
        return self.cachable

    def is_modified(self,cache_header):
        if cache_header is None:
            return True
        elif cache_header[0] is 'If-Modified-Since' and self.cache_id[0] is 'Last-Modified':
            return datetime.datetime.strptime(self.cache_id[1],CacheController.time_format) > datetime.datetime.strptime(cache_header[1],CacheController.time_format)
        elif cache_header[0] is 'If-None-Match' and self.cache_id[0] is 'Etag' :
            return cache_header[1] != self.cache_id[1]
        else:
            return True

    def get_cache_response_header(self):
        headers = {}
        if self.cachable :
            now = datetime.datetime.now()
            headers['Cache-Control'] = 'public, max-age='+str(self.age.total_seconds())
            headers['Expires'] = (now + self.age).strftime(CacheController.time_format)
            headers['Date'] = now.strftime(CacheController.time_format)
            headers[self.cache_id[0]] = self.cache_id[1]

        else:
            headers['Cache-Control'] = 'no-cache'

        return headers


