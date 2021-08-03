from config_dir import config
import logger
from logger import Level
from selenium import webdriver

from scrapers.life_coach_school import LifeCoachSchoolWebScraper
from scrapers.coaching_federation import FederationWebScraper
from configparser import ConfigParser

def main():
    config.load_config("config_dir/config.ini")
    logger.initialize_logger(Level.DETAIL_PLUS)
    driver = webdriver.Firefox()
    driver.set_page_load_timeout(60)
    # lcs = LifeCoachSchoolWebScraper(driver)
    # lcs.process_all_coaches()
    fcs = FederationWebScraper(driver)
    fcs.process_all_coaches()

if __name__ == '__main__':
    main()
