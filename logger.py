import sys
from enum import IntEnum

from utils.control_flow import fail_with_message_to_file as fail


class Level(IntEnum):
    CRITICAL = 1
    ERROR = 2
    WARNING = 3
    SUMMARY = 4
    DETAIL = 5
    DETAIL_PLUS = 6


class Logger:
    def __init__(self, log_level=1, log_file=None):
        self.log_level = log_level
        if not log_file:
            self.log_file = sys.stdout
        else:
            self.log_file = log_file

    def log(self, message, level):
        if level <= self.log_level:
            full_message = "{level:15} : {message}".format(
                level=level.name, message=message
            )
            print(full_message, file=self.log_file)


_LOGGER_STORE = {}


def does_logger_exist(logger="Global"):
    global _LOGGER_STORE
    return logger in _LOGGER_STORE


def get_logger(logger="Global"):
    global _LOGGER_STORE
    if logger not in _LOGGER_STORE:
        fail("Logger '" + logger + "' has not been initialized.")

    return _LOGGER_STORE[logger]


def initialize_logger(log_level, logger="Global", log_file=None):
    global _LOGGER_STORE
    if logger in _LOGGER_STORE:
        fail("Logger '" + logger + "' already exists.")

    _LOGGER_STORE[logger] = Logger(log_level, log_file)
