from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium_utils import scroll_to
from time import sleep

from coach_scraper import CoachScraper, LoadResult

class CoachElement:
    def __init__(self, root_div):
        self.root_div = root_div
        self.clickable_element = root_div.find_element_by_xpath("//div[@class='part1']/a")
        self.info_div = root_div.find_element_by_xpath("//*[@class='part2']")

class LifeCoachSchoolScraper(CoachScraper):
    def __init__(self, coaches):
        super().__init__(coaches, r"https://thelifecoachschool.com/directory/")
        self.driver = webdriver.Firefox()
        self.directory_loaded = False
        self.coach_elements = None
        self.directory_tab = None

    def load_directory(self):
        if not self.directory_loaded:
            self.driver.get(self.directory_url)
            self.directory_tab = self.driver.current_window_handle
            self.coach_elements = self.driver.find_elements_by_xpath("//*[@class='cmed_tiles_view_item']")

    def load_coach_set(self):
        pass

    def gather_coach_data(self, coach_num):
        if coach_num < len(self.coach_elements):
            coach_element = CoachElement(self.coach_elements[coach_num])
            scroll_to(self.driver, coach_element.clickable_element, y_offset=500)

            sleep(1)

            ActionChains(self.driver)\
                .move_to_element(coach_element.clickable_element)\
                .key_down(Keys.CONTROL)\
                .click(coach_element.clickable_element)\
                .key_up(Keys.CONTROL)\
                .perform()

            sleep(10)

            return LoadResult.SUCCESS