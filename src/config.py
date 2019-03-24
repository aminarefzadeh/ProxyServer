import json


class Config:

    class RestrictedHost:
        def __init__(self, json_object):
            self.url = json_object['URL']
            self.notify = json_object['notify']

        def __str__(self):
            return "URL: " + self.url + "\nnotify: " + str(self.notify)

    def __init__(self, config_path):
        # self.port = 8080

        with open(config_path) as json_file:
            data = json.load(json_file)

            self.host = data['host']
            self.port = data['port']

            # Restriction
            restriction_object = data['restriction']
            self.is_restricted = restriction_object['enable']
            self.restricted_hosts = []
            for json_object in restriction_object['targets']:
                self.restricted_hosts.append(Config.RestrictedHost(json_object))

            # Privacy
            privacy_object = data['privacy']
            self.must_provide_privacy = privacy_object['enable']
            self.privacy_user_agent = privacy_object['userAgent']

            # Logging
            logging_object = data['logging']
            self.must_log = logging_object['enable']
            self.clear_log = logging_object['clear']
            self.log_file_path = logging_object['logFile']

    def clear_log_file(self):
        return self.clear_log

    def get_log_file_path(self):
        if self.must_log:
            return self.log_file_path
        return None

    def get_user_agent(self):
        if self.must_provide_privacy:
            return self.privacy_user_agent
        return None
