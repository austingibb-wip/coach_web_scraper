from enum import Enum
from unittest import TestCase
from uuid import uuid4
import re
import csv

import logger
from logger import Level

from coach.validation.name import *
from coach.validation.email import *
from coach.validation.phone import *
from coach.validation.social import *
from coach.validation.url import *
from test_utils import test_setup
from utils import are_any


class CoachCert(Enum):
    ASSOCIATE = 1
    PROFESSIONAL = 2
    MASTER = 3
    LIFE = 4

    def __str__(self):
        if self == CoachCert.ASSOCIATE:
            return "Associate Certified Coach"
        elif self == CoachCert.PROFESSIONAL:
            return "Professional Certified Coach"
        elif self == CoachCert.MASTER:
            return "Master Certified Coach"
        elif self == CoachCert.LIFE:
            return "Life Coach School Certified"
        else:
            return "Unknown"


class CoachData:
    def __init__(
        self,
        source_url,
        first_name="",
        last_name="",
        full_name="",
        coach_cert=None,
        niche_description="",
        website_url="",
        email="",
        phone="",
        instagram_url="",
        linkedin_url="",
        twitter_url="",
    ):
        """
        Data object for all coach fields. Does coach and fails when:
            - source url is not present or is not a valid url.
            - certification is not None or a certification enum value.
        """
        self._logger = logger.get_logger()
        self._logs = []
        self._uuid = str(uuid4())

        self.log(Level.DETAIL_PLUS, "Constructor started.")

        if not source_url or not validate_url(source_url):
            message = "Source url not provided for coach."
            self.log(Level.CRITICAL, message)
            raise ValueError(message)
        if coach_cert is not None and not isinstance(coach_cert, CoachCert):
            message = "Bad coach certification value."
            self.log(Level.CRITICAL, message)
            raise ValueError(message)

        self.source_url = source_url
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        if (
            self.first_name.lower() not in self.full_name.lower()
            or self.last_name.lower() not in full_name.lower()
        ):
            message = "Bad full name. Must be a super-string of firstname/lastname."
            self.log(Level.CRITICAL, message)
            raise ValueError(message)

        self.coach_cert = coach_cert
        self.niche_description = niche_description
        self.website_url = validate_url_or_default(website_url)
        self.email = validate_email_or_default(email)
        self.phone = validate_phone_or_default(phone)
        if self.website_url != website_url:
            self.log(
                Level.ERROR,
                "Input error: website '"
                + website_url
                + "' changed to '"
                + self.website_url
                + "'",
            )
        if self.email != email:
            self.log(
                Level.ERROR,
                "Input error: email '" + email + "' changed to '" + self.email + "'",
            )
        if self.phone != phone:
            self.log(
                Level.ERROR,
                "Input error: phone '" + phone + "' changed to '" + self.phone + "'",
            )
        self.instagram_url = self.populate_social_media_url(
            ["instagram.com", "instagr.am"], instagram_url
        )
        self.linkedin_url = self.populate_social_media_url(
            ["linkedin.com", "linked.in"], linkedin_url, handle_prefix="in"
        )
        self.twitter_url = self.populate_social_media_url(["twitter.com"], twitter_url)

        self.data_snapshot()

        self.log(Level.DETAIL_PLUS, "Constructor done.")

    def get_data_elements(self):
        return [
            x
            for x in dir(self)
            if not x.startswith("__")
            and not x.startswith("_")
            and not callable(getattr(self, x))
        ]

    def data_snapshot(self, log=True):
        data_elements = self.get_data_elements()
        data_elements_log = "[ "
        for data_element in data_elements:
            data_elements_log += (
                data_element + "='" + str(getattr(self, data_element)) + "', "
            )
        data_elements_log = data_elements_log[0:-2]
        data_elements_log += " ]"
        if log:
            self.log(Level.SUMMARY, data_elements_log)
        return data_elements_log

    def populate_social_media_url(self, site_urls, social_media, handle_prefix=""):
        if not isinstance(site_urls, list) or len(site_urls) == 0:
            raise ValueError(
                "This is likely a programmer error, site_urls always need to be provided."
            )

        if not social_media:
            return ""

        for i in range(0, len(site_urls)):
            site_urls[i] = site_urls[i].lower()

        social_media = social_media.strip()
        if validate_url(social_media):  # is url
            if are_any.within(site_urls, social_media.lower()):
                return social_media
            else:
                message = (
                    "Social media url '"
                    + social_media
                    + "' doesn't match provided sites: "
                    + str(site_urls)
                )
                self.log(Level.ERROR, message)
                return ""
        elif validate_handle(social_media):  # is not url, is handle
            if social_media[0] == "@":
                social_media = social_media[1:]
            if handle_prefix:
                handle_prefix = "/" + handle_prefix

            # social media url isn't too important, just pick the first one
            constructed_url = (
                "https://" + site_urls[0] + handle_prefix + "/" + social_media
            )

            self.log(
                Level.DETAIL,
                "From handle '"
                + social_media
                + "' constructed url '"
                + constructed_url
                + "'",
            )
            return constructed_url
        else:
            self.log(
                Level.ERROR,
                "Social media was ignored for not being a valid site or handle '"
                + social_media
                + "'.",
            )
            return ""

    def log(self, log_level, message):
        self._logs.append((log_level, message))
        self._logger.log("[ Coach Data #" + self._uuid + " ] " + message, log_level)

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state["_logs"]
        del state["_logger"]
        return state

    def __setstate__(self, d):
        d["_logger"] = logger.get_logger()
        d["_logs"] = []
        self.__dict__ = d


class TestCoachData(TestCase):
    SOME_URL = "http://someurl.com"
    NON_URL = "badurl"
    SOME_HANDLE = "@thatguy"
    SOME_USER = "thatguy"

    SETUP_DONE = False

    def setUp(self):
        test_setup()

    def test_fail_no_source_url(self):
        with self.assertRaises(
            ValueError, msg="CoachData should fail with no source url."
        ):
            cd = CoachData("")

    def test_fail_bad_source_url(self):
        with self.assertRaises(
            ValueError, msg="CoachData should fail with invalid source url."
        ):
            cd = CoachData(TestCoachData.NON_URL)

    def test_good_source_url(self):
        try:
            cd = CoachData(TestCoachData.SOME_URL)
        except Exception:
            self.fail("Unexpected error for good source url.")

    def test_fail_bad_cert(self):
        with self.assertRaises(
            ValueError, msg="Non CoachCert should cause a system exit."
        ):
            cd = CoachData(TestCoachData.SOME_URL, coach_cert=54)

    def test_good_coach_cert(self):
        cd = CoachData(TestCoachData.SOME_URL, coach_cert=CoachCert.MASTER)
        self.assertEqual(
            cd.coach_cert,
            CoachCert.MASTER,
            "Unexpected value when assigning coach cert to enum CoachCert.",
        )

    def test_invalid_email(self):
        cd = CoachData(TestCoachData.SOME_URL, email=TestCoachData.NON_URL)
        self.assertEqual(
            cd.email, "", "Email should be empty when provided address is invalid."
        )

    def test_invalid_website(self):
        cd = CoachData(TestCoachData.SOME_URL, website_url=TestCoachData.NON_URL)
        self.assertEqual(
            cd.website_url, "", "Website should be empty when provided url is invalid."
        )

    def test_data_snapshot(self):
        data = {
            "source_url": "somecoachdirectory.com",
            "first_name": "rick",
            "last_name": "sanches",
            "full_name": "rick Gargler Sanches",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Basketball, Dance",
            "website_url": "betterthanyoucoaching.com",
            "email": "rick.sanches@btycoaching.com",
            "linkedin_url": "ricksanches",
        }

        cd = CoachData(**data)

        datasnapshot = cd.data_snapshot(log=False)
        for key in data:
            if key in ["first_name", "last_name", "full_name"]:
                data[key] = data[key]

            if key not in datasnapshot or str(data[key]) not in datasnapshot:
                self.fail(
                    "Data value or key is missing from coach data snapshot. "
                    + key
                    + ": "
                    + str(data[key])
                )


class TestCoachDataSocialMedia(TestCase):
    def setUp(self):
        test_setup()

    def test_invalid_social_media(self):
        cd = CoachData(TestCoachData.SOME_URL, twitter_url="test@gmail.com")
        self.assertEqual(
            cd.twitter_url,
            "",
            "Twitter url should be empty when provided url/handle are invalid.",
        )

    def test_valid_twitter_url(self):
        twitter_user_url = "twitter.com/" + TestCoachData.SOME_USER
        cd = CoachData(TestCoachData.SOME_URL, twitter_url=twitter_user_url)
        self.assertEqual(
            cd.twitter_url,
            twitter_user_url,
            "Twitter url should be considered valid and stored.",
        )

    def test_non_twitter_url(self):
        twitter_user_url = "wrongwebsite.com/" + TestCoachData.SOME_USER
        cd = CoachData(TestCoachData.SOME_URL, twitter_url=twitter_user_url)
        self.assertEqual(
            cd.twitter_url,
            "",
            "Twitter url should be empty when provided website doesn't contain twitter.com.",
        )

    def test_valid_twitter_handle(self):
        cd = CoachData(TestCoachData.SOME_URL, twitter_url=TestCoachData.SOME_HANDLE)
        expected_url = "https://twitter.com/" + TestCoachData.SOME_HANDLE[1:]
        self.assertEqual(
            cd.twitter_url,
            expected_url,
            "Twitter handle should be considered valid and stored as url.",
        )

    def test_valid_instagram_url(self):
        instagram_user_url = "instagram.com/" + TestCoachData.SOME_USER
        cd = CoachData(TestCoachData.SOME_URL, instagram_url=instagram_user_url)
        self.assertEqual(
            cd.instagram_url,
            instagram_user_url,
            "Instagram url should be accepted if it contains instagr.am",
        )

    def test_valid_alt_instagram_url(self):
        instagram_user_url = "instagr.am/" + TestCoachData.SOME_USER
        cd = CoachData(TestCoachData.SOME_URL, instagram_url=instagram_user_url)
        self.assertEqual(
            cd.instagram_url,
            instagram_user_url,
            "Instagram url should be accepted if it contains instagr.am",
        )

    def test_non_instagram_url(self):
        instagram_user_url = "nongram.com/" + TestCoachData.SOME_USER
        cd = CoachData(TestCoachData.SOME_URL, instagram_url=instagram_user_url)
        self.assertEqual(
            cd.instagram_url,
            "",
            "Linkedin url should be empty when provided website doesn't contain linkedin.com.",
        )

    def test_valid_linkedin_url(self):
        linkedin_user_url = "https://linkedin.com/in/" + TestCoachData.SOME_URL
        cd = CoachData(TestCoachData.SOME_URL, linkedin_url=linkedin_user_url)
        self.assertEqual(
            cd.linkedin_url,
            linkedin_user_url,
            "Linkedin url should be accepted if it contains linkedin.com",
        )

    def test_valid_linkedin_alt_url(self):
        linkedin_user_url = "https://linked.in/in/" + TestCoachData.SOME_URL
        cd = CoachData(TestCoachData.SOME_URL, linkedin_url=linkedin_user_url)
        self.assertEqual(
            cd.linkedin_url,
            linkedin_user_url,
            "Linkedin url should be accepted if it contains linked.in",
        )

    def test_non_linkedin_url(self):
        linkedin_user_url = "https://wrongin.com/in/" + TestCoachData.SOME_URL
        cd = CoachData(TestCoachData.SOME_URL, linkedin_url=linkedin_user_url)
        self.assertEqual(
            cd.linkedin_url,
            "",
            "Linkedin url should be empty when provided website doesn't contain linkedin.com.",
        )

    def test_linkedin_handle_prefix(self):
        linkedin_user_handle = TestCoachData.SOME_HANDLE
        cd = CoachData(TestCoachData.SOME_URL, linkedin_url=linkedin_user_handle)
        expected_url = "https://linkedin.com/in/" + TestCoachData.SOME_HANDLE[1:]
        self.assertEqual(
            cd.linkedin_url,
            expected_url,
            "The /in/ handle prefix may not be added properly to url or url is wrong in some way.",
        )
