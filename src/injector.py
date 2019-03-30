

from bs4 import BeautifulSoup

class Injector():
    def __init__(self,config,response):
        self.config = config
        self.response = response

    def inject(self):

        if not self.response.valid:
            return self.response.raw_data
        if self.response.status != 200:
            return self.response.raw_data
        if 'text/html' not in self.response.http_request_data.get('Content-Type', ''):
            return self.response.raw_data

        if self.config.must_inject:
            soup = BeautifulSoup(self.response.body, 'html.parser')
            injection_element = soup.new_tag('p', id='ProxyInjection')
            injection_element.attrs['style'] = 'background-color:brown; height:40px; width:100%; position:fixed; ' \
                                               'top:0px; left:0px; margin:0px; padding: 15px 0 0 0;' \
                                               'z-index: 1060; text-align: center; color: white'
            injection_element.insert(0, self.config.injection_body)
            if soup.body:
                soup.body.insert(0, injection_element)
                self.response.body = soup.prettify()

        return self.response.convert_to_message()
