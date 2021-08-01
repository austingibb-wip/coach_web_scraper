from abc import ABC, abstractmethod
from enum import Enum

from config_dir import config
import logger

class LoadResult(Enum):
    SUCCESS = 0
    SKIP = 1
    ERROR = 2

class CoachScraper(ABC):
    def __init__(self, directory_url):
        self.coaches = []
        self.directory_url = directory_url
        self.logger = logger.get_logger()
        self.retries = int(config.read("GENERAL", "COACH_RETRIES_BEFORE_FAIL"))

    @abstractmethod
    def load_all_coaches(self):
        pass
