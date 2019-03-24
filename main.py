import sys
from config import Config
from server import Server


def main():
    config = Config(sys.argv[1])
    server = Server(config)
    server.start_server()


if __name__ == '__main__':
    main()
