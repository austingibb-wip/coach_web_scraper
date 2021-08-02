from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from coach_data_writer import write_coach_to_csv, write_coach_data
from selenium_utils import scroll_to
from time import sleep
import os

import logger
from logger import Level
from coach_data import CoachData, CoachCert
from config_dir import config
from utils import retry, fail, extract_name
from test_utils import test_setup
from persistant_coach_processor import PersistentCoachProcessor

class LifeCoachSchoolScraper:
    def __init__(self, csv_file_path=None):
        self.directory_url = r"https://thelifecoachschool.com/directory/"
        self.driver = webdriver.Firefox()
        self.logger = logger.get_logger()
        self.retries = int(config.read("GENERAL", "COACH_RETRIES_BEFORE_FAIL"))
        self.csv_file_path = csv_file_path
        if self.csv_file_path is None:
            self.csv_file_path = config.read("GENERAL", "CSV_FILE_PATH")
        object_file_path = config.read("LIFE_COACH_SCHOOL_SCRAPER", "OBJECTS_PATH")
        flag_file_path = config.read("LIFE_COACH_SCHOOL_SCRAPER", "FLAG_PATH")
        self.persistant_processor = PersistentCoachProcessor(object_file_path, flag_file_path)

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
            coaches_processed = 0
            self.logger.log("Coaches to process:" + str(coaches_to_process), Level.SUMMARY)
            keys = list(self.persistant_processor.objects_dict.keys())
            for coach_href in keys:
                coach_data = self.gather_coach_data(coach_href)
                if coach_data is None:
                    continue

                write_coach_to_csv(coach_data)
                write_coach_data(coach_data)
                self.persistant_processor.object_processed(coach_href)
                coaches_processed += 1
                self.logger.log("Progress: " + str(coaches_processed) + " / " + str(coaches_to_process) + " - " + \
                                "{:.3f}".format(coaches_processed/coaches_to_process) + "%", Level.SUMMARY)
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

    def gather_coach_data(self, coach_href):
        coach_data = None

        def inner_gather():
            nonlocal coach_data
            self.driver.get(coach_href)

            full_name, first_name, last_name = self.gather_name()
            coach_cert = self.gather_coach_cert()
            niche = self.gather_niche()
            website = self.gather_website()
            email, phone = self.gather_contact_info()
            instagram_url, linkedin_url, twitter_url = self.gather_social_media()

            coach_data = CoachData(
                source_url=coach_href,
                full_name=full_name,
                first_name=first_name,
                last_name=last_name,
                coach_cert=coach_cert,
                niche_description=niche,
                website_url=website,
                email=email,
                phone=phone,
                instagram_url=instagram_url,
                twitter_url=twitter_url,
                linkedin_url=linkedin_url
            )

        try:
            result = retry(inner_gather, self.retries)
        except:
            result = False

        if not result:
            message = "Could not gather coach data: " + coach_href
            self.logger.log(message, Level.ERROR)
            return None

        self.logger.log("Coach successfully gathered." + coach_href, Level.DETAIL)

        return coach_data

    def gather_name(self):
        try:
            full_name = self.driver.find_element_by_xpath("//div[@class='cmed-title']").text.lower()
            first, last = extract_name(full_name)
            if full_name is None:
                raise Exception()
        except Exception as e:
            msg = "Unable to get name of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            raise e
        self.logger.log("Gathered name: " + first + " " + last, Level.DETAIL_PLUS)
        return full_name, first, last

    def gather_coach_cert(self):
        try:
            coach_cert_text = self.driver.find_element_by_xpath("//div[@id='information-box']/ul[@class='cmed-box-taxonomy'][1]/li[2]").text
            coach_cert_text = coach_cert_text.lower()
            if coach_cert_text.lower() == "certified life coach":
                coach_cert = CoachCert.LIFE
            elif coach_cert_text.lower() == "master certified coach":
                coach_cert = CoachCert.MASTER
            else:
                self.logger.log("Coach unexpectedly had no certification class.", Level.ERROR)
                coach_cert = None
        except Exception as e:
            msg = "Unable to get name of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            return None

        self.logger.log("Gathered cert: " + str(coach_cert), Level.DETAIL_PLUS)
        return coach_cert

    def gather_niche(self):
        try:
            niche_lines = self.driver.find_elements_by_xpath("//div[@id='information-box']/ul[@class='cmed-box-taxonomy'][2]/li")
            niche_lines = niche_lines[1:]
            niche = ", ".join([line.text for line in niche_lines])
        except NoSuchElementException as e:
            msg = "This coach does not have a niche description."
            self.logger.log(msg, Level.DETAIL)
            return None
        except Exception as e:
            msg = "Unable to get niche of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            return None

        self.logger.log("Gathered niche: " + niche, Level.DETAIL_PLUS)
        return niche

    def gather_website(self):
        coach_href = self.driver.current_url
        try:
            wesbite_href = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Website']").get_attribute("href")
            self.driver.get(wesbite_href)
            website = self.driver.current_url
        except NoSuchElementException as e:
            msg = "This coach does not have a website."
            self.logger.log(msg, Level.DETAIL_PLUS)
            return ""
        except Exception as e:
            msg = "Unable to get website of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            return ""
        finally:
            if self.driver.current_url != coach_href:
                self.driver.get(coach_href)

        self.logger.log("Gathered website: " + website, Level.DETAIL_PLUS)
        return website

    def gather_contact_info(self):
        try:
            email = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Contact']").get_attribute("href")
            if email.startswith("mailto:"):
                email = email[7:]
        except NoSuchElementException as e:
            msg = "This coach does not have an available email."
            self.logger.log(msg, Level.DETAIL_PLUS)
            return "", ""
        except Exception as e:
            msg = "Unable to get email of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            email = ""

        phone = ""

        self.logger.log("Gathered contact info. email: " + email + " phone:" + phone, Level.DETAIL_PLUS)
        return email, phone

    def gather_social_media(self):
        try:
            instagram = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Instagram']").get_attribute(
                "href")
        except NoSuchElementException as e:
            msg = "This coach does not have an instagram."
            self.logger.log(msg, Level.DETAIL_PLUS)
            instagram = ""
        except Exception as e:
            msg = "Unable to get instagram of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            instagram = ""

        try:
            linkedin = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Linkedin ']").get_attribute(
                "href")
        except NoSuchElementException as e:
            msg = "This coach does not have a linkedin."
            self.logger.log(msg, Level.DETAIL_PLUS)
            linkedin = ""
        except Exception as e:
            msg = "Unable to get linkedin of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            linkedin = ""

        try:
            twitter = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Twitter']").get_attribute(
                "href")
        except NoSuchElementException as e:
            msg = "This coach does not have a twitter."
            self.logger.log(msg, Level.DETAIL_PLUS)
            twitter = ""
        except Exception as e:
            msg = "Unable to get twitter of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            twitter = ""

        self.logger.log("Gathered social media. instagram: " + instagram + \
                        " twitter: " + twitter + " linkedin: " + linkedin, Level.DETAIL_PLUS)

        return instagram, linkedin, twitter


class TestLifeCoachSchoolScraper(TestCase):
    def setUp(self):
        test_setup()

    def test_gather_name(self):
        test_href = "https://thelifecoachschool.com/certified-coach/patti-britt-campbell/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        full_name, first_name, last_name = lcs.gather_name()
        self.assertEqual(full_name, "patti britt campbell")
        self.assertEqual(first_name, "patti")
        self.assertEqual(last_name, "campbell")

    def test_gather_coach_cert(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        coach_cert = lcs.gather_coach_cert()
        self.assertEqual(coach_cert, CoachCert.LIFE)

    def test_gather_niche(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        niche = lcs.gather_niche()
        self.assertEqual("Health & Wellness, Other", niche)

    def test_gather_website(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        website = lcs.gather_website()
        self.assertEqual("https://www.vanessafayefoerster.com/", website)

    def test_gather_contact_info(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        email, phone = lcs.gather_contact_info()
        self.assertEqual("vanessa@vanessafayefoerster.com", email)

    def test_gather_social_media(self):
        test_href = "https://thelifecoachschool.com/certified-coach/anusha-streubel/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        instagram, linkedin, twitter = lcs.gather_social_media()
        self.assertEqual(instagram, "https://www.instagram.com/releasetheoverwhelm/")
        self.assertEqual(linkedin, "http://www.linkedin.com/in/anusha-hemachandra-streubel-md-mph-4814a75")
        self.assertEqual(twitter, "https://twitter.com/anushastreubel")

    def test_scrape_single_coach(self):
        lcs = LifeCoachSchoolScraper()
        lcs.load_coaches_from_directory()

        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        cd = lcs.gather_coach_data(test_href)
        self.assertEqual(cd.source_url, test_href)
        self.assertEqual(cd.first_name, "Vanessa")
        self.assertEqual(cd.last_name, "Foerster")
        self.assertEqual(cd.full_name, "Vanessa Foerster")
        self.assertEqual(cd.coach_cert, CoachCert.LIFE)
        self.assertEqual(cd.niche_description, "Health & Wellness, Other")
        self.assertEqual(cd.website_url, "https://www.vanessafayefoerster.com/")
        self.assertEqual(cd.email, "vanessa@vanessafayefoerster.com")
        self.assertEqual(cd.instagram_url, "https://www.instagram.com/vanessafayefoerster/?hl=en")
        self.assertEqual(cd.linkedin_url, "")
        self.assertEqual(cd.twitter_url, "")

