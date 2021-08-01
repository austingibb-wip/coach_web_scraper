from configparser import ConfigParser

_CONFIG = None

def load_config(file):
    global _CONFIG
    config = ConfigParser()
    config.read(file)
    _CONFIG = config

def is_config_loaded():
    global _CONFIG
    return _CONFIG is not None

def read(section, option):
    global _CONFIG
    return _CONFIG[section][option]
