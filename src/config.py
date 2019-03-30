import json


class Config:

    class RestrictedHost:
        def __init__(self, json_object):
            self.url = json_object['URL']
            self.notify = json_object['notify']

        def __str__(self):
            return "URL: " + self.url + "\nnotify: " + str(self.notify)

    def __init__(self, config_path):
        with open(config_path) as json_file:
            data = json.load(json_file)

            self.host = data['host']
            self.port = data['port']

            # Restriction
            restriction_object = data['restriction']
            self.is_restricted = restriction_object['enable']
            self.admin_data = restriction_object['adminData']

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

            injection_object = data['HTTPInjection']
            self.must_inject = injection_object['enable']
            self.injection_body = injection_object['post']['body']

            cache_object = data['caching']
            self.cache_enable = cache_object['enable']
            self.cache_size = cache_object['size']

            accounting_object = data['accounting']
            self.user_accounts = { user['IP'] : user['volume'] for user in accounting_object['users']}

    def get_server_name(self):
        return self.privacy_user_agent

    def get_admin_data_path(self):
        return self.admin_data

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
