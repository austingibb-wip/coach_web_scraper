from config_dir import config
import logger
from logger import Level
from selenium import webdriver

from sites.coaching_federation.cf_scraper import FederationWebScraper


def main():
    config.load_config("config_dir/config.ini")
    logger.initialize_logger(Level.DETAIL_PLUS)
    driver = webdriver.Firefox()
    driver.set_page_load_timeout(60)
    # lcs = LifeCoachSchoolWebScraper(driver)
    # lcs.process_all_coaches()
    fcs = FederationWebScraper(driver)
    fcs.process_all_coaches()


if __name__ == "__main__":
    main()
