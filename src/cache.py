
from src.logger import Logger
from src.forward import forward
from src.response import ProxyResponse

class CacheHandler():
    def __init__(self,config):
        self.cache_enable = config.cache_enable

    def parseRequest(self,proxy_request):

        if self.cache_enable and proxy_request.method == "GET": # cachable check "GET" and "no-cache"
            key = proxy_request.addr
            cache_response = LRUCache.get(key)
            cache_response = ProxyResponse()
            if not cache_response is -1:   # we have data in our cache

                cache_header = proxy_request.get_cache_header() # header like ('if-modified-since') sended by user

                if not cache_response.cache.is_expire():  # and it's not expire yet
                    Logger.log_message("Cache HIT")

                    if cache_response.cache.is_modified(cache_header):
                        return cache_response
                    else:
                        return CacheHandler.get_304_response(cache_response.cache.get_cache_response_header())

                else: # cache date expired check it again

                    proxy_request.clear_cache_header()
                    request_cache_header = cache_response.cache.get_cache_request_header()
                    proxy_request.http_request_data[request_cache_header[0]] = request_cache_header[1]

                    proxy_response = forward(proxy_request)

                    if proxy_response != None and proxy_response.valid :
                        if proxy_response.status == 304:
                            cache_response.cache.update_cache(proxy_response.cache)
                            LRUCache.set(key,cache_response)
                            Logger.log_message("Cache HIT")
                            if cache_response.cache.is_modified(cache_header):
                                return cache_response
                            else:
                                return CacheHandler.get_304_response(cache_response.cache.get_cache_response_header())

                        elif proxy_response.cache.is_cachable():  # check status == 200 and can cache
                            LRUCache.set(key, proxy_response)  # caching data

                            if proxy_response.cache.is_modified(cache_header):
                                return proxy_response
                            else:
                                return CacheHandler.get_304_response(proxy_response.cache.get_cache_response_header())

                        else:
                            LRUCache.pop(key)
                            Logger.log_message("Cache pop element !!")

                    else:
                        LRUCache.pop(key)
                        Logger.log_message("Cache pop element 2 !!")

                    return proxy_response
            else:
                proxy_response = forward(proxy_request)
                if proxy_response != None and proxy_response.valid and proxy_response.cache.is_cachable():
                    LRUCache.set(key,proxy_response)   #caching data

                return proxy_response
        else:
            return forward(proxy_request)

    @staticmethod
    def get_304_response(http_header):
        response_304 = ProxyResponse()
        response_304.status = 304
        response_304.message = "Not Modified"
        response_304.http_request_data = http_header

        return response_304




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
    def pop(key):
        LRUCache.rlock.acquire()
        try:
            LRUCache.cache.pop(key)
        except KeyError:
            pass
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