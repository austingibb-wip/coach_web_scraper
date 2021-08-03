from collections import OrderedDict
from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities, ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep

from coach_data_writer import write_coach_to_csv, write_coach_data
from coach_scraper import CoachScraper

import logger
from logger import Level
from coach_data import CoachData, CoachCert
from config_dir import config
from utils import retry, fail, extract_name
from test_utils import test_setup
from persistant_coach_processor import PersistentCoachProcessor


class FederationCoachScraper(CoachScraper):
    def __init__(self, driver):
        super().__init__(driver)

    def _gather_name(self, data):
        full_name = self.driver.find_element_by_xpath("//h2[@id='coachName']").text.lower()
        first, last = extract_name(full_name)
        if full_name is None:
            raise Exception()
        return full_name, first, last

    def _gather_coach_cert(self, data):
        return None

    def _gather_niche(self, data):
        niche_lines = self.driver.find_elements_by_xpath(
            "//div[@id='detailsTabContent']//table/tbody/tr/td[text()='Coaching Themes']/following-sibling::td[1]/div")
        niche = ", ".join([line.text for line in niche_lines])
        return niche

    def _gather_website(self, data):
        website = self.driver.find_element_by_xpath("//div[@id='contactTabContent']//label[text()='Web Site']/following-sibling::a")\
            .get_attribute("href")
        if not website:
            website = ""
        return website

    def _gather_email(self, data):
        email = self.driver.find_element_by_xpath("//div[@id='contactTabContent']//label[text()='Email Address']/following-sibling::a")\
            .get_attribute("href")
        if email.startswith("mailto:"):
            email = email[7:]
        return email

    def _gather_phone(self, data):
        phone = self.driver.find_element_by_xpath("//div[@id='contactTabContent']//label[text()='Phone']/following-sibling::span")\
            .text
        return phone

    def _gather_instagram(self, data):
        instagram = self.driver.find_element_by_xpath("//div[@id='socialLinks']//a[@id='instagramLink']")\
            .get_attribute("href")
        return instagram

    def _gather_linkedin(self, data):
        linkedin = self.driver.find_element_by_xpath("//div[@id='socialLinks']//a[@id='linkedInLink']")\
            .get_attribute("href")
        return linkedin

    def _gather_twitter(self, data):
        twitter = self.driver.find_element_by_xpath("//div[@id='socialLinks']//a[@id='twitterLink']")\
            .get_attribute("href")
        return twitter


class FederationWebScraper:
    def __init__(self, driver, csv_file_path=None):
        self.directory_url = r"https://apps.coachingfederation.org/eweb/ccfdynamicpage.aspx?webcode=ccfsearch&site=icfapp"
        self.coach_href_prefix = r"https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey="
        self.driver = driver
        self.logger = logger.get_logger()
        self.retries = int(config.read("GENERAL", "COACH_RETRIES_BEFORE_FAIL"))
        self.csv_file_path = csv_file_path
        if self.csv_file_path is None:
            self.csv_file_path = config.read("COACHING_FEDERATION_SCRAPER", "CSV_FILE_PATH")
        object_file_path = config.read("COACHING_FEDERATION_SCRAPER", "OBJECTS_PATH")
        self.persistent_processor = PersistentCoachProcessor(object_file_path)

    def process_all_coaches(self):
        self.driver.get(self.directory_url)
        self.setup_filters()
        if not self.persistent_processor.is_initialized():
            num_pages = self.get_num_pages()
            pages_to_process = OrderedDict()
            for page in range(1, num_pages+1):
                pages_to_process[page] = page
            self.persistent_processor.initialize(pages_to_process)

        keys = list(self.persistent_processor.objects_dict.keys())
        coaches_to_process = 50
        for page_num in keys:
            self.logger.log("Page progress: " + str(page_num) + " / " + str(keys[-1]), Level.SUMMARY)
            coaches_processed = 1
            self.goto_page(page_num)
            sleep(3)
            coach_cards = self.driver.find_elements_by_xpath("//div[@id='cards']/div/div[@class='content']//input")
            coaches = []

            for card in coach_cards:
                coach_value = card.get_attribute("value")
                coach_href = self.coach_href_prefix + coach_value
                self.driver.execute_script("""window.open("","_blank");""")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                timed_out = False
                try:
                    self.driver.get(coach_href)
                except TimeoutException:
                    self.logger.log("Coach page load timeout.", Level.ERROR)
                    timed_out = True
                if not timed_out:
                    federation_scraper = FederationCoachScraper(self.driver)
                    coach_data = federation_scraper.gather_coach_data(coach_href, None)
                    if coach_data is not None:
                        coaches.append(coach_data)
                self.driver.execute_script("""window.close();""")
                self.driver.switch_to.window(self.driver.window_handles[0])
                self.logger.log("Progress: " + str(coaches_processed) + " / " + str(coaches_to_process) + " - " + \
                                "{:.3f}".format(coaches_processed / coaches_to_process * 100) + "%", Level.DETAIL)
                self.logger.log("Page progress: " + str(page_num) + " / " + str(keys[-1]), Level.DETAIL)
                coaches_processed += 1
                if timed_out or coach_data is None:
                    break
            if timed_out or coach_data is None:
                continue

            if len(coaches) == len(coach_cards) and len(coaches) > 0:
                for coach_data in coaches:
                    write_coach_data(coach_data)
                    write_coach_to_csv(coach_data, config.read("COACHING_FEDERATION_SCRAPER", "CSV_FILE_PATH"))
                self.persistent_processor.object_processed(page_num)

    def setup_filters(self):
        dropdown = self.driver.find_element_by_xpath("//div[@id='filter-group-demographics']/a")
        dropdown.click()
        sleep(0.5)
        language_button = self.driver.find_element_by_xpath("//button[@id='add-fluent-language']")
        language_button.click()
        sleep(0.5)
        english_button = self.driver.find_element_by_xpath("//button[@data-value='English']")
        english_button.click()
        english_button.send_keys(Keys.ESCAPE)
        sleep(2)
        location_button = self.driver.find_element_by_xpath("//button[@id='add-location']")
        location_button.click()
        sleep(0.5)
        search_bar = self.driver.find_element_by_xpath("//input[@id='countries-search']")
        search_bar.send_keys("United States")
        search_bar.send_keys(Keys.ENTER)
        sleep(0.5)
        usa_button = self.driver.find_element_by_xpath("//button[@data-display='United States']")
        usa_button.click()
        sleep(1)
        self.driver.find_elements_by_xpath("//button[text()='Close']")[1].click()
        sleep(2)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        self.driver.find_element_by_xpath("//div[@id='paging-dropdown']").click()
        sleep(0.5)
        self.driver.find_element_by_xpath("//div[@id='paging']//div[@data-value='50']").click()
        sleep(2)

    def get_num_pages(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        return int(self.driver.find_element_by_xpath("//div[@id='paging']//a[@class='item'][last()]").text.strip())

    def goto_page(self, page_num):
        page_num_button = None
        while page_num_button is None:
            sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            try:
                page_num_button = self.driver.find_element_by_xpath("//a[@data-value='{page_num}']".format(page_num=page_num))
            except NoSuchElementException:
                self.driver.find_element_by_xpath("//div[@id='paging']//a[@class='item active']/following-sibling::a[2]").click()

        page_num_button.click()

    # def load_coaches_from_directory(self):
    #     coach_hrefs = None
    #
    #     def inner_load():
    #         nonlocal coach_hrefs
    #         self.logger.log("Trying to gather directory: " + self.directory_url, Level.SUMMARY)
    #         self.driver.get(self.directory_url)
    #         coach_elements = self.driver.find_elements_by_xpath("//*[@class='cmed_tiles_view_item']//*[@class='part1']/a")
    #         coach_hrefs = [ce.get_attribute("href") for ce in coach_elements]
    #
    #     result = retry(inner_load, max_tries=self.retries)
    #     if not result:
    #         message = "Could not load directory: " + self.directory_url
    #         self.logger.log(message, Level.CRITICAL)
    #         raise RuntimeError(message)
    #
    #     return coach_hrefs


class TestFederationCoachScraper(TestCase):
    TEST_DRIVER = None

    def setUp(self):
        test_setup()
        if not TestFederationCoachScraper.TEST_DRIVER:
            TestFederationCoachScraper.TEST_DRIVER = webdriver.Firefox()

    def test_gather_name(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        full_name, first_name, last_name = fcs.gather_name()
        self.assertEqual(full_name, "mr. daniel r. abbatiello, pcc, rev.")
        self.assertEqual(first_name, "daniel")
        self.assertEqual(last_name, "abbatiello")

    def test_gather_niche(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        niche = fcs.gather_niche()
        self.assertEqual("Interpersonal Relationships, Personal Growth, Self Confidence", niche)

    def test_gather_website(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=389078A5-7ED9-4AAA-91E5-D018C458B58E"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        website = fcs.gather_website()
        self.assertEqual("http://www.abdein.com/", website)

    def test_gather_email(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        email = fcs.gather_email()
        self.assertEqual("dabbatiello@maine.rr.com", email)

    def test_gather_phone(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        phone = fcs.gather_phone()
        self.assertEqual("207.655.4406", phone)

    def test_gather_social_media(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=03D15412-BE53-41E0-826C-5996A6FF6EE2"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        instagram, linkedin, twitter = fcs.gather_social_media()
        self.assertEqual(instagram, "")
        self.assertEqual(linkedin, "https://www.linkedin.com/in/parleyacker/")
        self.assertEqual(twitter, "https://twitter.com/CareerWon")

    def test_gather_no_social_media(self):
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        fcs.driver.get(test_href)
        instagram, linkedin, twitter = fcs.gather_social_media()
        self.assertEqual(instagram, "")
        self.assertEqual(linkedin, "")
        self.assertEqual(twitter, "")

    def test_scrape_single_coach(self):
        driver = TestFederationCoachScraper.TEST_DRIVER
        fcs = FederationCoachScraper(TestFederationCoachScraper.TEST_DRIVER)
        test_href = "https://apps.coachingfederation.org/eweb/CCFDynamicPage.aspx?webcode=ccfcoachprofileview&coachcstkey=E4D2ADC4-63D1-4702-932C-AEB7EDAE2790"
        driver.get(test_href)
        cd = fcs.gather_coach_data(test_href)
        self.assertEqual(cd.source_url, test_href)
        self.assertEqual(cd.first_name, "Daniel")
        self.assertEqual(cd.last_name, "Abbatiello")
        self.assertEqual(cd.full_name, "Mr. Daniel R. Abbatiello, Pcc, Rev.")
        self.assertEqual(cd.coach_cert, None)
        self.assertEqual(cd.niche_description, "Interpersonal Relationships, Personal Growth, Self Confidence")
        self.assertEqual(cd.website_url, "")
        self.assertEqual(cd.email, "dabbatiello@maine.rr.com")
        self.assertEqual(cd.instagram_url, "")
        self.assertEqual(cd.linkedin_url, "")
        self.assertEqual(cd.twitter_url, "")