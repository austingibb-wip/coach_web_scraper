from unittest import TestCase
import csv
import pickle
import os

from config_dir import config
from coach.data import CoachData, CoachCert
from test_utils import test_setup
from utils.files import atomic_write

HEADER_ROW = [
    "First Name",
    "Last Name",
    "Full Name",
    "Certification",
    "Niche",
    "Website",
    "Email",
    "Instagram",
    "Twitter",
    "Linkedin",
    "Source URL",
]


def write_coach_data(coach_data, coach_data_storage_path=None):
    if coach_data_storage_path is None:
        coach_data_storage_path = config.read("GENERAL", "COACH_DATA_STORAGE_PATH")

    coach_data_list = None

    def init_coach_data_file(coach_data_file):
        pickle.dump([], coach_data_file, protocol=pickle.HIGHEST_PROTOCOL)

    def read_coach_data_file(coach_data_file):
        nonlocal coach_data_list
        coach_data_list = pickle.load(coach_data_file)
        coach_data_list.append(coach_data)

    def modify_coach_data_file(coach_data_file):
        nonlocal coach_data_list
        pickle.dump(
            coach_data_list, coach_data_file, protocol=pickle.HIGHEST_PROTOCOL
        )

    atomic_write(coach_data_storage_path, init_file=init_coach_data_file, read_file=read_coach_data_file, modify_file=modify_coach_data_file)



def write_header_row(csv_file_path=None):
    if csv_file_path is None:
        csv_file_path = config.read("GENERAL", "CSV_FILE_PATH")
    global HEADER_ROW
    with open(csv_file_path, "a+") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(HEADER_ROW)


def write_coach_to_csv(coach, csv_file_path):
    with open(csv_file_path, "a+") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                coach.first_name,
                coach.last_name,
                coach.full_name,
                str(coach.coach_cert),
                coach.niche_description,
                coach.website_url,
                coach.email,
                coach.instagram_url,
                coach.twitter_url,
                coach.linkedin_url,
                coach.source_url,
            ]
        )


class WriteCoachesTest(TestCase):
    @staticmethod
    def coach_data_to_expected_csv_row(cd):
        return '{first_name},{last_name},{full_name},{coach_cert},"{niche_description}",{website_url},{email},{instagram_url},{twitter_url},{linkedin_url},{source_url}\n'.format(
            first_name=cd.first_name,
            last_name=cd.last_name,
            full_name=cd.full_name,
            coach_cert=str(cd.coach_cert),
            niche_description=cd.niche_description,
            website_url=cd.website_url,
            email=cd.email,
            instagram_url=cd.instagram_url,
            twitter_url=cd.twitter_url,
            linkedin_url=cd.linkedin_url,
            source_url=cd.source_url,
        )

    def setUp(self):
        test_setup()
        with open(config.read("TEST", "TEST_CSV_FILE_PATH"), "w+") as test_csv_file:
            test_csv_file.write("")
        coach_data_storage_path = config.read("TEST", "TEST_COACH_DATA_STORAGE_PATH")
        if os.path.exists(coach_data_storage_path):
            os.remove(coach_data_storage_path)

    def test_write_to_csv(self):
        global HEADER_ROW
        raw_data_1 = {
            "source_url": "coachdir.com/coach_one",
            "full_name": "Coach Middle One",
            "first_name": "Coach",
            "last_name": "One",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, One, Things",
            "website_url": "coachone.com",
            "email": "coach.one@coachone.com",
            "instagram_url": "coachone",
            "twitter_url": "coachone",
            "linkedin_url": "coachone",
        }

        raw_data_2 = {
            "source_url": "coachdir.com/coach_two",
            "full_name": "Coach Middle Two",
            "first_name": "Coach",
            "last_name": "Two",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, Two, Things",
            "website_url": "coachtwo.com",
            "email": "coach.two@coachtwo.com",
            "instagram_url": "coachtwo",
            "twitter_url": "coachtwo",
            "linkedin_url": "coachtwo",
        }

        raw_data_3 = {
            "source_url": "coachdir.com/coach_three",
            "full_name": "Coach Middle Three",
            "first_name": "Coach",
            "last_name": "Three",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, Three, Things",
            "website_url": "coachthree.com",
            "email": "coach.three@coachthree.com",
            "instagram_url": "coachthree",
            "twitter_url": "coachthree",
            "linkedin_url": "coachthree",
        }

        cd1 = CoachData(**raw_data_1)
        cd2 = CoachData(**raw_data_2)
        cd3 = CoachData(**raw_data_3)

        csv_file_path = config.read("TEST", "TEST_CSV_FILE_PATH")

        write_header_row(csv_file_path)
        write_coach_to_csv(cd1, csv_file_path)
        write_coach_to_csv(cd2, csv_file_path)
        write_coach_to_csv(cd3, csv_file_path)

        expected_csv_data = (
            ",".join(HEADER_ROW)
            + "\n"
            + self.coach_data_to_expected_csv_row(cd1)
            + self.coach_data_to_expected_csv_row(cd2)
            + self.coach_data_to_expected_csv_row(cd3)
        )

        with open(csv_file_path, "r") as csv_file:
            csv_file_contents = csv_file.read()
            self.assertEqual(expected_csv_data, csv_file_contents)

    def test_write_coach(self):
        raw_data_1 = {
            "source_url": "coachdir.com/coach_one",
            "full_name": "Coach Middle One",
            "first_name": "Coach",
            "last_name": "One",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, One, Things",
            "website_url": "coachone.com",
            "email": "coach.one@coachone.com",
            "instagram_url": "coachone",
            "twitter_url": "coachone",
            "linkedin_url": "coachone",
        }
        raw_data_2 = {
            "source_url": "coachfunky.com/coach_two",
            "full_name": "Coach Middle Two",
            "first_name": "Coach",
            "last_name": "Two",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, Two, Things",
            "website_url": "coachtwo.com",
            "email": "coach.two@coachtwo.com",
            "instagram_url": "coachtwo",
            "twitter_url": "coachtwo",
            "linkedin_url": "coachtwo",
        }

        cd1 = CoachData(**raw_data_1)
        coach_data_storage_path = config.read("TEST", "TEST_COACH_DATA_STORAGE_PATH")
        write_coach_data(cd1, coach_data_storage_path=coach_data_storage_path)
        with open(coach_data_storage_path, "rb") as coach_data_storage:
            cd_list = pickle.load(coach_data_storage)
            self.assertEqual(len(cd_list), 1)
            self.assertEqual(cd_list[0].first_name, "Coach")
            self.assertEqual(cd_list[0].last_name, "One")
            self.assertEqual(cd_list[0].instagram_url, "https://instagram.com/coachone")

        cd2 = CoachData(**raw_data_2)
        write_coach_data(cd2, coach_data_storage_path=coach_data_storage_path)
        with open(coach_data_storage_path, "rb") as coach_data_storage:
            cd_list = pickle.load(coach_data_storage)
            self.assertEqual(len(cd_list), 2)
            self.assertEqual(cd_list[0].first_name, "Coach")
            self.assertEqual(cd_list[0].last_name, "One")
            self.assertEqual(cd_list[0].instagram_url, "https://instagram.com/coachone")
            self.assertEqual(cd_list[1].first_name, "Coach")
            self.assertEqual(cd_list[1].last_name, "Two")
            self.assertEqual(cd_list[1].instagram_url, "https://instagram.com/coachtwo")
