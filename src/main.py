import sys

import logging

from src.config import Config
from src.logger import Logger
from src.server import Server


def main():
    config = Config(sys.argv[1])
    Logger.initialize_logger(config)

    Logger.log_message("Proxy server launched")
    server = Server(config)
    server.start_server()


if __name__ == '__main__':
    main()
