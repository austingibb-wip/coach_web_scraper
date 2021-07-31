# abstract class
# load coach source page
# load set of coaches
# for each coach
# isolate coach, read coach data

from abc import ABC, abstractmethod
from enum import Enum
import time

import coach_data
from utils import fail

class LoadResult(Enum):
    SUCCESS = 0
    RETRY = 1
    FAIL = 2
    END_OF_DATA = 3

class CoachScraper(ABC):
    def __init__(self, coaches, directory_url):
        self.coaches = []
        self.directory_url = directory_url

    def load_all_coaches(self):
        coach_set = 0
        while True:
            self.load_directory()
            result = self.load_coach_set()
            if result == LoadResult.FAIL:
                fail("Failed to load coach set.")
            elif result == LoadResult.RETRY:
                time.sleep(2)
                continue
            else: # success
                coach_set += 1

            coach_num = 0
            while True:
                result, coach_data = self.gather_coach_data(coach_num)
                if result == LoadResult.FAIL:
                    fail("Failed to load coach data.")
                elif result == LoadResult.RETRY:
                    time.sleep(2)
                    continue
                elif result == LoadResult.END_OF_DATA:
                    break
                else: # success
                    self.coaches.append(coach_data)
                    coach_num += 1

    @abstractmethod
    def load_directory(self):
        pass

    @abstractmethod
    def load_coach_set(self):
        pass

    @abstractmethod
    def gather_coach_data(self, num):
        pass