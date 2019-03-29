
from src.socketutils import SocketUtils
from src.logger import Logger
from src.response import ProxyResponse
from src.request import ProxyRequest
import socket


def forward(proxy_request):
    forward_socket = establish_forwarding_socket(proxy_request)
    if forward_socket is None:
        return None

    forward_socket.send(proxy_request.convert_to_message().encode('ascii', 'ignore'))
    forward_socket.settimeout(2)
    forward_response = SocketUtils.recv_all(forward_socket)
    forward_socket.close()

    proxy_response = ProxyResponse(forward_response)
    Logger.log_packet(str(proxy_response), "Server Response")

    return proxy_response


def establish_forwarding_socket(proxy_request):
    proxy_port = proxy_request.host_port
    hostname = proxy_request.host_name
    host_ip = socket.gethostbyname(hostname)

    try:
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        return None

    forward_socket.settimeout(2)
    try:
        forward_socket.connect((host_ip, proxy_port))

    except Exception:
        forward_socket.close()
        return None

    return forward_socket