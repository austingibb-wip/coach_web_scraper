import logger
from config_dir import config
import os


def test_setup():
    if not logger.does_logger_exist():
        logger.initialize_logger(logger.Level.DETAIL_PLUS)
    if not config.is_config_loaded():
        config.load_config("config_dir/config.ini")
