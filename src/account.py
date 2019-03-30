from threading import RLock


class AccountHandler:
    def __init__(self):
        pass

    user_dict = None
    lock = RLock()

    @staticmethod
    def set_config(config):
        AccountHandler.user_dict = config.user_accounts.copy()

    @staticmethod
    def can_access(user_address):
        ip = user_address[0]
        access = False

        AccountHandler.lock.acquire()
        if ip in AccountHandler.user_dict:
            access = AccountHandler.user_dict[ip] > 0
        AccountHandler.lock.release()

        return access

    @staticmethod
    def sub_volume(address, value):
        ip = address[0]

        AccountHandler.lock.acquire()
        if ip in AccountHandler.user_dict:
            AccountHandler.user_dict[ip] -= value
        AccountHandler.lock.release()
