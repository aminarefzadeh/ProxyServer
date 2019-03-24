import sys

import logging

from config import Config
from server import Server
from src.logger import Logger


def main():
    config = Config(sys.argv[1])
    Logger.initialize_logger(config)

    Logger.log_message("Proxy server launched")
    server = Server(config)
    server.start_server()


if __name__ == '__main__':
    main()
