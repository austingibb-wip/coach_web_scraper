# run scraping engine
# take list of labelled rows
# write to CSV
from config_dir import config
import logger
from logger import Level

from scrapers.life_coach_school import LifeCoachSchoolScraper
from configparser import ConfigParser

def main():
    config.load_config("config_dir/config.ini")
    logger.initialize_logger(Level.DETAIL_PLUS)
    lcs = LifeCoachSchoolScraper()
    lcs.process_all_coaches()


if __name__ == '__main__':
    main()
