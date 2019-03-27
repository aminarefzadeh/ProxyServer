import logging
import os


class Logger:
    log_enable = True

    def __init__(self):
        pass

    @staticmethod
    def initialize_logger(config):
        if config.get_log_file_path() is None:
            Logger.log_enable = False
            return

        Logger.log_enable = True
        log_file_path = config.get_log_file_path()

        if config.clear_log_file():
            try:
                os.remove(log_file_path)
            except:
                pass

        logging.basicConfig(filename=log_file_path,
                            level=logging.INFO,
                            format='[%(asctime)s] %(message)s',
                            datefmt='%d/%b/%Y %I:%M:%S %H:%M:%S')

    @staticmethod
    def log_message(message):
        if not Logger.log_enable:
            return

        logging.info(message)

    @staticmethod
    def log_packet(message, title):
        output_message = "%s\n----------------------------------------------------------------------\n" % title
        output_message += message.decode("utf-8", "ignore")
        output_message += "\n----------------------------------------------------------------------"
        logging.info(output_message)
