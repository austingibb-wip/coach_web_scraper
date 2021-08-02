# run scraping engine
# take list of labelled rows
# write to CSV
from config_dir import config
import logger
from logger import Level
from csv_writer import write_coaches_to_csv

from scrapers.life_coach_school import LifeCoachSchoolScraper
from configparser import ConfigParser

def main():
    config.load_config("config_dir/config.ini")
    logger.initialize_logger(Level.DETAIL)
    csv_file_path = config.read("GENERAL", "CSV_FILE_PATH")
    lcs = LifeCoachSchoolScraper()
    coaches = lcs.load_all_coaches()
    write_coaches_to_csv(csv_file_path=csv_file_path, coaches=coaches)


if __name__ == '__main__':
    main()
