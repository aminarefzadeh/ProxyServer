import json


class Config:
    def __init__(self, config_path):
        # self.host = '127.0.0.1'
        # self.port = 8080
        with open(config_path) as json_file:
            data = json.load(json_file)
            self.host = data['host']
            self.port = data['port']
            # print data
