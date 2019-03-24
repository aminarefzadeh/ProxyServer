from threading import Thread


class Restricts:
    def __init__(self, config):
        self.is_restricted = config.is_restricted
        self.restricted_hosts = config.restricted_hosts
        # TODO give server name from config
        self.server_name = "CN Proxy Server (v1.0.0)"
        self.admin_mail = "this will refactored"

    def check_access(self, http_request):
        rule = None

        if not self.is_restricted:
            return rule

        for restricted_host in self.restricted_hosts:
            if http_request.http_request_data['Host'] == restricted_host.url:
                rule = restricted_host

        return rule

    def send_disallow_response(self, socket, client_message):
        http_message = "<!DOCTYPE html>"\
                       "<html>"\
                       "<head><title>Access Denied</title></head>"\
                       "<body>"\
                       "<h1>You are not allowed to access this site</h1>"\
                       "</body>"\
                       "</html>"

        message = "HTTP/1.1 407 Proxy Authentication Required\r\n"
        message += "Server: " + self.server_name + "\r\n"
        message += "Content-Type: text/html; charset=utf-8"
        message += "Content-Length: " + str(len(http_message)) + "\r\n"
        message += "Connection: Closed \r\n"
        message += "\r\n"
        message += http_message

        socket.send(message.encode('ascii', 'ignore'))
        socket.close()

        email_agent = Restricts.EmailAgent(client_message)
        email_agent.start()

    class EmailAgent(Thread):
        def __init__(self, client_message):
            Thread.__init__(self)
            self.client_message = client_message

        def run(self):
            # TODO : Mail message

            print("this is a email to admin")



