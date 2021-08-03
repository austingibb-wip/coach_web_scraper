from unittest import TestCase

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from coach_data_writer import write_coach_to_csv, write_coach_data
from coach_scraper import CoachScraper

import logger
from logger import Level
from coach_data import CoachData, CoachCert
from config_dir import config
from utils import retry, fail, extract_name
from test_utils import test_setup
from persistant_coach_processor import PersistentCoachProcessor

class LifeCoachSchoolCoachScraper(CoachScraper):
    def __init__(self, driver):
        super().__init__(driver)

    def _gather_name(self, data):
        full_name = self.driver.find_element_by_xpath("//div[@class='cmed-title']").text.lower()
        first, last = extract_name(full_name)
        if full_name is None:
            raise Exception()
        return full_name, first, last

    def _gather_coach_cert(self, data):
        coach_cert_text = self.driver.find_element_by_xpath(
            "//div[@id='information-box']/ul[@class='cmed-box-taxonomy'][1]/li[2]").text
        coach_cert_text = coach_cert_text.lower()
        if coach_cert_text.lower() == "certified life coach":
            coach_cert = CoachCert.LIFE
        elif coach_cert_text.lower() == "master certified coach":
            coach_cert = CoachCert.MASTER
        else:
            self.logger.log("Coach unexpectedly had no certification class.", Level.ERROR)
            coach_cert = None
        return coach_cert

    def _gather_niche(self, data):
        niche_lines = self.driver.find_elements_by_xpath(
            "//div[@id='information-box']/ul[@class='cmed-box-taxonomy'][2]/li")
        niche_lines = niche_lines[1:]
        niche = ", ".join([line.text for line in niche_lines])
        return niche

    def _gather_website(self, data):
        website = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Website']").get_attribute(
            "href")
        return website

    def _gather_email(self, data):
        email = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Contact']").get_attribute(
            "href")
        if email.startswith("mailto:"):
            email = email[7:]
        return email

    def _gather_phone(self, data):
        return ""

    def _gather_contact(self, type):
        return self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='{type}']".format(type=type)) \
            .get_attribute("href")

    def _gather_instagram(self, data):
        instagram = self._gather_contact("Instagram")
        return instagram

    def _gather_linkedin(self, data):
        linkedin = self._gather_contact("Linkedin ")
        return linkedin

    def _gather_twitter(self, data):
        twitter = self._gather_contact("Twitter")
        return twitter

class LifeCoachSchoolWebScraper:
    def __init__(self, driver, csv_file_path=None):
        self.directory_url = r"https://thelifecoachschool.com/directory/"
        self.driver = driver
        self.logger = logger.get_logger()
        self.retries = int(config.read("GENERAL", "COACH_RETRIES_BEFORE_FAIL"))
        self.csv_file_path = csv_file_path
        if self.csv_file_path is None:
            self.csv_file_path = config.read("LIFE_COACH_SCHOOL_SCRAPER", "CSV_FILE_PATH")
        object_file_path = config.read("LIFE_COACH_SCHOOL_SCRAPER", "OBJECTS_PATH")
        self.persistant_processor = PersistentCoachProcessor(object_file_path)

    def process_all_coaches(self):
        try:
            if not self.persistant_processor.is_initialized():
                self.logger.log("Initializing coaches.", Level.SUMMARY)
                coach_hrefs = self.load_coaches_from_directory()
                objects_dict = {}
                for coach_href in coach_hrefs:
                    objects_dict[coach_href] = coach_href
                self.persistant_processor.initialize(objects=objects_dict)
                self.logger.log("Coach hrefs loaded and persisted.", Level.SUMMARY)
            else:
                self.logger.log("Coach objects already exist on file, not initializing.", Level.SUMMARY)

            coaches_to_process = len(self.persistant_processor.objects_dict)
            coaches_processed = 1
            self.logger.log("Coaches to process:" + str(coaches_to_process), Level.SUMMARY)
            keys = list(self.persistant_processor.objects_dict.keys())
            for coach_href in keys:
                self.driver.get(coach_href)
                lcs_coach_scraper = LifeCoachSchoolCoachScraper(self.driver)
                coach_data = lcs_coach_scraper.gather_coach_data(coach_href)
                if coach_data is None:
                    continue

                write_coach_to_csv(coach_data)
                write_coach_data(coach_data)
                self.persistant_processor.object_processed(coach_href)
                coaches_processed += 1
                self.logger.log("Progress: " + str(coaches_processed) + " / " + str(coaches_to_process) + " - " + \
                                "{:.3f}".format(coaches_processed/coaches_to_process*100) + "%", Level.SUMMARY)
        finally:
            self.logger.log("Processed " + str(coaches_processed) + " out of " + str(coaches_to_process), Level.SUMMARY)

    def load_coaches_from_directory(self):
        coach_hrefs = None

        def inner_load():
            nonlocal coach_hrefs
            self.logger.log("Trying to gather directory: " + self.directory_url, Level.SUMMARY)
            self.driver.get(self.directory_url)
            coach_elements = self.driver.find_elements_by_xpath("//*[@class='cmed_tiles_view_item']//*[@class='part1']/a")
            coach_hrefs = [ce.get_attribute("href") for ce in coach_elements]

        result = retry(inner_load, max_tries=self.retries)
        if not result:
            message = "Could not load directory: " + self.directory_url
            self.logger.log(message, Level.CRITICAL)
            raise RuntimeError(message)

        return coach_hrefs


class TestLifeCoachSchoolCoachScraper(TestCase):
    TEST_DRIVER = None

    def setUp(self):
        test_setup()
        if not TestLifeCoachSchoolCoachScraper.TEST_DRIVER:
            TestLifeCoachSchoolCoachScraper.TEST_DRIVER = webdriver.Firefox()

    def test_gather_name(self):
        test_href = "https://thelifecoachschool.com/certified-coach/patti-britt-campbell/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        full_name, first_name, last_name = lcs.gather_name()
        self.assertEqual(full_name, "patti britt campbell")
        self.assertEqual(first_name, "patti")
        self.assertEqual(last_name, "campbell")

    def test_gather_coach_cert(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        coach_cert = lcs.gather_coach_cert()
        self.assertEqual(coach_cert, CoachCert.LIFE)

    def test_gather_niche(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        niche = lcs.gather_niche()
        self.assertEqual("Health & Wellness, Other", niche)

    def test_gather_website(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        website = lcs.gather_website()
        self.assertEqual(
            "https://thelifecoachschool.com/certified-coach/vanessa-foerster/?cmedid=21481&cmedkey=2a7e45a8c8", website)

    def test_gather_email(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        email = lcs.gather_email()
        self.assertEqual("vanessa@vanessafayefoerster.com", email)

    def test_gather_social_media(self):
        test_href = "https://thelifecoachschool.com/certified-coach/anusha-streubel/"
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        lcs.driver.get(test_href)
        instagram, linkedin, twitter = lcs.gather_social_media()
        self.assertEqual(instagram, "https://www.instagram.com/releasetheoverwhelm/")
        self.assertEqual(linkedin, "http://www.linkedin.com/in/anusha-hemachandra-streubel-md-mph-4814a75")
        self.assertEqual(twitter, "https://twitter.com/anushastreubel")

    def test_scrape_single_coach(self):
        driver = TestLifeCoachSchoolCoachScraper.TEST_DRIVER
        lcs = LifeCoachSchoolCoachScraper(TestLifeCoachSchoolCoachScraper.TEST_DRIVER)
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        driver.get(test_href)
        cd = lcs.gather_coach_data(test_href)
        self.assertEqual(cd.source_url, test_href)
        self.assertEqual(cd.first_name, "Vanessa")
        self.assertEqual(cd.last_name, "Foerster")
        self.assertEqual(cd.full_name, "Vanessa Foerster")
        self.assertEqual(cd.coach_cert, CoachCert.LIFE)
        self.assertEqual(cd.niche_description, "Health & Wellness, Other")
        self.assertEqual(cd.website_url, "https://thelifecoachschool.com/certified-coach/vanessa-foerster/?cmedid=21481&cmedkey=2a7e45a8c8")
        self.assertEqual(cd.email, "vanessa@vanessafayefoerster.com")
        self.assertEqual(cd.instagram_url, "https://www.instagram.com/vanessafayefoerster/?hl=en")
        self.assertEqual(cd.linkedin_url, "")
        self.assertEqual(cd.twitter_url, "")

