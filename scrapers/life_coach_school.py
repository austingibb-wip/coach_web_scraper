from unittest import TestCase

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium_utils import scroll_to
from time import sleep

from coach_scraper import CoachScraper, LoadResult
import logger
from logger import Level
from coach_data import CoachData, CoachCert
from config_dir import config
from utils import retry, fail, extract_name

class LifeCoachSchoolScraper(CoachScraper):
    def __init__(self):
        super().__init__(r"https://thelifecoachschool.com/directory/")
        self.driver = webdriver.Firefox()
        self.coach_hrefs = None
        self.coach_filter_file_path = config.read("LIFE_COACH_SCHOOL_SCRAPER", "ERROR_FILTER_FILE")
        self.href_coach_filter = self.load_href_coach_filter()
        self.filter_file = open(self.coach_filter_file_path, "w+")

    def load_href_coach_filter(self):
        href_coach_filter = set()
        with open(self.coach_filter_file_path, "r") as filter_file:
            for line in filter_file:
                href_coach_filter.add(line.strip())
        return href_coach_filter

    def load_all_coaches(self):
        self.load_directory()
        for coach_href in self.coach_hrefs:
            if len(self.href_coach_filter) > 0 and coach_href not in self.href_coach_filter:
                continue

            coach, result = self.gather_coach_data(coach_href)
            if result == LoadResult.SKIP:
                continue
            elif result == LoadResult.SUCCESS:
                self.coaches.append(coach)
            elif result == LoadResult.ERROR:
                return None

        return self.coaches

    def load_directory(self):
        def inner_load():
            self.logger.log("Trying to gather directory: " + self.directory_url, Level.SUMMARY)
            self.driver.get(self.directory_url)
            coach_elements = self.driver.find_elements_by_xpath("//*[@class='cmed_tiles_view_item']//*[@class='part1']/a")
            self.coach_hrefs = [ce.get_attribute("href") for ce in coach_elements]

        result = retry(inner_load, max_tries=self.retries)
        if not result:
            message = "Could not load directory: " + self.directory_url
            self.logger.log(message, Level.CRITICAL)
            fail(message)

        self.logger.log("Directory successfully gathered: " + self.directory_url, Level.SUMMARY)

    def log_bad_coach(self, coach_href):
        self.filter_file.write(coach_href + "\n")
        self.filter_file.flush()

    def gather_coach_data(self, coach_href):
        coach_data = None

        def inner_gather():
            nonlocal coach_data
            self.driver.get(coach_href)

            first_name, last_name = self.gather_name()
            coach_cert = self.gather_coach_cert()
            niche = self.gather_niche()
            website = self.gather_website()
            email, phone = self.gather_contact_info()
            instagram_url, linkedin_url, twitter_url = self.gather_social_media()

            coach_data = CoachData(
                source_url=coach_href,
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
            self.log_bad_coach(coach_href)
            return None, LoadResult.SKIP

        self.logger.log("Coach successfully gathered." + coach_href, Level.DETAIL)

        return coach_data, LoadResult.SUCCESS

    def gather_name(self):
        try:
            first, last = extract_name(self.driver.find_element_by_xpath("//div[@class='cmed-title']").text)
            if first is None:
                raise Exception()
        except Exception as e:
            msg = "Unable to get name of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            raise e
        self.logger.log("Gathered name: " + first + " " + last, Level.DETAIL_PLUS)
        return first, last

    def gather_coach_cert(self):
        try:
            coach_cert = None
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
            self.logger.log(msg, Level.DETAIL)
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
            msg = "This coach does not have a website."
            self.logger.log(msg, Level.WARNING)
            return "", ""
        except Exception as e:
            msg = "Unable to get email of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            email = ""

        phone = ""
        return email, phone

    def gather_social_media(self):
        try:
            instagram = self.driver.find_element_by_xpath("//div[@id='contact-box']/ul//*[text()='Instagram']").get_attribute(
                "href")
        except NoSuchElementException as e:
            msg = "This coach does not have an instagram."
            self.logger.log(msg, Level.WARNING)
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
            self.logger.log(msg, Level.WARNING)
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
            self.logger.log(msg, Level.WARNING)
            twitter = ""
        except Exception as e:
            msg = "Unable to get twitter of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            twitter = ""

        return instagram, linkedin, twitter


class TestLifeCoachSchoolScraper(TestCase):
    def setUp(self):
        if not logger.does_logger_exist():
            logger.initialize_logger(logger.Level.DETAIL_PLUS)
        if not config.is_config_loaded():
            config.load_config("config_dir/config.ini")

    def test_gather_name(self):
        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        lcs = LifeCoachSchoolScraper()
        lcs.driver.get(test_href)
        first_name, last_name = lcs.gather_name()
        self.assertEqual(first_name, "Vanessa")
        self.assertEqual(last_name, "Foerster")

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
        lcs.load_directory()

        test_href = "https://thelifecoachschool.com/certified-coach/vanessa-foerster/"
        cd = lcs.gather_coach_data(test_href)
        self.assertEqual(cd.source_url, test_href)
        self.assertEqual(cd.first_name, "Vanessa")
        self.assertEqual(cd.last_name, "Foerster")
        self.assertEqual(cd.coach_cert, CoachCert.LIFE)
        self.assertEqual(cd.niche_description, "Health & Wellness, Other")
        self.assertEqual(cd.website_url, "https://www.vanessafayefoerster.com/")
        self.assertEqual(cd.email, "vanessa@vanessafayefoerster.com")
        self.assertEqual(cd.instagram_url, "https://www.instagram.com/vanessafayefoerster/?hl=en")
        self.assertEqual(cd.linkedin_url, "")
        self.assertEqual(cd.twitter_url, "")



