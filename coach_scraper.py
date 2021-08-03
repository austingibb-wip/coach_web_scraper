from abc import ABC, abstractmethod
from selenium.common.exceptions import NoSuchElementException
import traceback

from config_dir import config
import logger
from logger import Level
from coach_data import CoachData
from coach_data_writer import write_coach_to_csv, write_coach_data
from utils import retry, normalize_phone, normalize_name

class CoachScraper(ABC):
    def __init__(self, driver):
        self.driver = driver
        self.logger = logger.get_logger()
        self.retries = int(config.read("GENERAL", "COACH_RETRIES_BEFORE_FAIL"))

    def gather_coach_data(self, source_url, data=None):
        coach_data = None

        def inner_gather():
            nonlocal coach_data
            full_name, first_name, last_name = self.gather_name(data)
            coach_cert = self.gather_coach_cert(data)
            niche = self.gather_niche(data)
            website = self.gather_website(data)
            email = self.gather_email(data)
            phone = self.gather_phone(data)
            instagram_url, linkedin_url, twitter_url = self.gather_social_media(data)

            coach_data = CoachData(
                source_url=source_url,
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

        def inner_gather_fail():
            self.logger.log("Error gathering coach data.", Level.ERROR)
            self.logger.log(traceback.format_exc(), Level.ERROR)

        result = retry(inner_gather, self.retries, on_exception=inner_gather_fail)

        if not result:
            message = "Could not gather coach data: " + source_url
            self.logger.log(message, Level.ERROR)
            return None

        self.logger.log("Coach successfully gathered." + source_url, Level.DETAIL)

        return coach_data

    def gather_name(self, data=None):
        try:
            full_name, first, last = self._gather_name(data)
            full_name = normalize_name(full_name)
            first = normalize_name(first)
            last = normalize_name(last)
        except Exception as e:
            msg = "Unable to get name of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            raise e
        self.logger.log("Gathered name: " + first + " " + last, Level.DETAIL_PLUS)
        return full_name, first, last

    @abstractmethod
    def _gather_name(self, data):
        pass

    def gather_coach_cert(self, data=None):
        try:
            coach_cert = self._gather_coach_cert(data)
        except Exception as e:
            msg = "Unable to get name of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            return None

        self.logger.log("Gathered cert: " + str(coach_cert), Level.DETAIL_PLUS)
        return coach_cert

    @abstractmethod
    def _gather_coach_cert(self, data):
        pass

    def gather_niche(self, data=None):
        try:
            niche = self._gather_niche(data)
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

    @abstractmethod
    def _gather_niche(self, data):
        pass

    def gather_website(self, data=None):
        try:
            website = self._gather_website(data)
        except NoSuchElementException as e:
            msg = "This coach does not have a website."
            self.logger.log(msg, Level.DETAIL_PLUS)
            return ""
        except Exception as e:
            msg = "Unable to get website of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            return ""

        self.logger.log("Gathered website: " + website, Level.DETAIL_PLUS)
        return website

    @abstractmethod
    def _gather_website(self, data):
        pass

    def gather_email(self, data=None):
        try:
            email = self._gather_email(data)
        except NoSuchElementException as e:
            msg = "This coach does not have an available email."
            self.logger.log(msg, Level.DETAIL_PLUS)
            return ""
        except Exception as e:
            msg = "Unable to get email of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            email = ""

        self.logger.log("Gathered email: " + email, Level.DETAIL_PLUS)
        return email

    @abstractmethod
    def _gather_email(self, data):
        pass

    def gather_phone(self, data=None):
        try:
            phone = normalize_phone(self._gather_phone(data))
        except NoSuchElementException as e:
            msg = "This coach does not have an available phone number."
            self.logger.log(msg, Level.DETAIL_PLUS)
            return ""
        except Exception as e:
            msg = "Unable to get phone number of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            phone = ""

        self.logger.log("Gathered phone number: " + phone, Level.DETAIL_PLUS)
        return phone

    @abstractmethod
    def _gather_phone(self, data):
        pass

    def gather_social_media(self, data=None):
        try:
            instagram = self._gather_instagram(data)
        except NoSuchElementException as e:
            msg = "This coach does not have an instagram."
            self.logger.log(msg, Level.DETAIL_PLUS)
            instagram = ""
        except Exception as e:
            msg = "Unable to get instagram of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            instagram = ""

        try:
            linkedin = self._gather_linkedin(data)
        except NoSuchElementException as e:
            msg = "This coach does not have a linkedin."
            self.logger.log(msg, Level.DETAIL_PLUS)
            linkedin = ""
        except Exception as e:
            msg = "Unable to get linkedin of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            linkedin = ""

        try:
            twitter = self._gather_twitter(data)
        except NoSuchElementException as e:
            msg = "This coach does not have a twitter."
            self.logger.log(msg, Level.DETAIL_PLUS)
            twitter = ""
        except Exception as e:
            msg = "Unable to get twitter of coach: " + str(e)
            self.logger.log(msg, Level.ERROR)
            twitter = ""

        self.logger.log("Gathered social media. Instagram: '" + instagram + "'" +
                        " Twitter: '" + twitter + "' Linkedin: '" + linkedin + "'", Level.DETAIL_PLUS)

        return instagram, linkedin, twitter

    @abstractmethod
    def _gather_instagram(self, data):
        pass

    @abstractmethod
    def _gather_linkedin(self, data):
        pass

    @abstractmethod
    def _gather_twitter(self, data):
        pass