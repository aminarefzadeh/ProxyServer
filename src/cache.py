
from src.request import ClientRequest,ProxyRequest
from src.response import ProxyResponse
from src.logger import Logger
from src.socketutils import SocketUtils
import socket

class CacheHandler():
    def __init__(self,config):
        self.cache_enable = config.cache_enable

    def parseRequest(self,client_request):
        if self.cache_enable:
            return None
        else:
            proxy_request = ProxyRequest(client_request)

            forward_socket = CacheHandler.establish_forwarding_socket(client_request)
            if forward_socket is None:
                return None

            forward_socket.send(proxy_request.convert_to_message().encode('ascii', 'ignore'))
            forward_socket.settimeout(2)
            forward_response = SocketUtils.recv_all(forward_socket)
            forward_socket.close()

            proxy_response = ProxyResponse(forward_response)
            Logger.log_packet(str(proxy_response), "Server Response")

            return proxy_response

    @staticmethod
    def establish_forwarding_socket(proxy_request):
        proxy_port = 80
        if ":" in proxy_request.http_request_data["Host"]:
            hostname = proxy_request.http_request_data["Host"].split(':')[0]
            proxy_port = int(proxy_request.http_request_data["Host"].split(':')[1])
        else:
            hostname = proxy_request.http_request_data["Host"]

        host_ip = socket.gethostbyname(hostname)

        try:
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            return None

        forward_socket.settimeout(1)
        try:
            forward_socket.connect((host_ip, proxy_port))

        except Exception:
            forward_socket.close()
            return None

        return forward_socket




import collections
from threading import RLock

class LRUCache:

    capacity = 200
    cache = collections.OrderedDict()
    rlock = RLock()

    @staticmethod
    def get(key):
        LRUCache.rlock.acquire()
        value = -1
        try:
            value = LRUCache.cache.pop(key)
            LRUCache.cache[key] = value
        except KeyError:
            value = -1
        LRUCache.rlock.release()
        return value

    @staticmethod
    def set(key, value):
        LRUCache.rlock.acquire()
        try:
            LRUCache.cache.pop(key)
        except KeyError:
            if len(LRUCache.cache) >= LRUCache.capacity:
                LRUCache.cache.popitem(last=False)
        LRUCache.cache[key] = value
        LRUCache.rlock.release()

    @staticmethod
    def set_capacity(value):
        LRUCache.capacity = value

#
# class LRUCache:
#     def __init__(self, capacity):
#         self.capacity = capacity
#         self.tm = 0
#         self.cache = {}
#         self.lru = {}
#
#     def get(self, key):
#         if key in self.cache:
#             self.lru[key] = self.tm
#             self.tm += 1
#             return self.cache[key]
#         return -1
#
#     def set(self, key, value):
#         if len(self.cache) >= self.capacity:
#             # find the LRU entry
#             old_key = min(self.lru.keys(), key=lambda k:self.lru[k])
#             self.cache.pop(old_key)
#             self.lru.pop(old_key)
#         self.cache[key] = value
#         self.lru[key] = self.tm
#         self.tm += 1