from threading import Thread
from socket import *
import ssl
import base64

from src.logger import Logger


class Restricts:
    def __init__(self, config):
        self.is_restricted = config.is_restricted
        self.restricted_hosts = config.restricted_hosts
        self.server_name = config.get_server_name()
        self.admin_data_file = config.get_admin_data_path()

    def check_access(self, http_request):
        rule = None

        if not self.is_restricted:
            return rule

        for restricted_host in self.restricted_hosts:
            if http_request.http_request_data['Host'] == restricted_host.url:
                rule = restricted_host

        return rule

    def send_disallow_response(self, socket, client_message, notify):
        http_message = "<!DOCTYPE html>" \
                       "<html>" \
                       "<head><title>Access Denied</title></head>" \
                       "<body>" \
                       "<h1>You are not allowed to access this site</h1>" \
                       "</body>" \
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
        Logger.log_message('Packet Dropped')
        if notify:
            email_agent = Restricts.EmailAgent(client_message, self.admin_data_file)
            email_agent.start()

    class EmailAgent(Thread):
        def __init__(self, client_message, admin_data_file):
            Thread.__init__(self)
            self.client_message = client_message
            self.admin_data_file = admin_data_file

        def run(self):
            mail_server = 'smtp.gmail.com'
            mail_port = 465

            client_socket = socket(AF_INET, SOCK_STREAM)
            wrapped_socket = ssl.wrap_socket(client_socket, ssl_version=ssl.PROTOCOL_TLSv1,
                                             ciphers='HIGH:-aNULL:-eNULL:-PSK:RC4-SHA:RC4-MD5')

            wrapped_socket.connect((mail_server, mail_port))

            wrapped_socket.recv(1024)
            hello_command = 'HELO hellogoogle\r\n'
            wrapped_socket.send(hello_command.encode())
            wrapped_socket.recv(1024)

            with open(self.admin_data_file, 'r') as admin_file:
                username = admin_file.readline()[0:-1]
                password = admin_file.readline()

            if username == '' or password == '':
                Logger.log_message('Email have not been sent.')

            up = base64.b64encode(("\000" + username + "\000" + password).encode())

            up = up.decode('utf-8', 'ignore').strip("\n")
            login = 'AUTH PLAIN ' + up + '\r\n'
            wrapped_socket.send(login.encode())
            wrapped_socket.recv(1024)

            from_command = 'MAIL FROM: <' + username + '>\r\n'
            wrapped_socket.send(from_command.encode())
            wrapped_socket.recv(1024)

            receiver = 'zangenehsaeed412@gmail.com'
            to_command = 'RCPT TO: <' + receiver + '>\r\n'
            wrapped_socket.send(to_command.encode())
            wrapped_socket.recv(1024)

            data_command = 'DATA\r\n'
            wrapped_socket.send(data_command.encode())
            wrapped_socket.recv(1024)
            subject = 'Restricted Proxy Access'
            body = 'We have just received a restricted http request. The Request is as below: \n' \
                   + self.client_message.convert_to_message()
            wrapped_socket.send(("Subject: " + subject + "\r\n\r\n" + body + "\r\n\r\n.\r\n" + "\r\n").encode())
            wrapped_socket.recv(1024)

            wrapped_socket.send("QUIT\r\n".encode())
            wrapped_socket.recv(1024)
            wrapped_socket.close()

            Logger.log_message('Email have been sent successfully')
