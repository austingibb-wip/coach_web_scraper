from unittest import TestCase
import csv

from config_dir import config
import logger
from coach_data import CoachData, CoachCert

HEADER_ROW = ["First Name", "Last Name", "Certification", "Niche", "Website", "Email", "Instagram", "Twitter", "Linkedin", "Source URL"]

def write_coaches_to_csv(coaches, csv_file_path):
    global HEADER_ROW
    with open(csv_file_path, "a+") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(HEADER_ROW)
        for coach in coaches:
            csv_writer.writerow([
                coach.first_name,
                coach.last_name,
                str(coach.coach_cert),
                coach.niche_description,
                coach.website_url,
                coach.email,
                coach.instagram_url,
                coach.twitter_url,
                coach.linkedin_url,
                coach.source_url
            ])

class WriteCoachesToCsvTest(TestCase):
    @staticmethod
    def coach_data_to_expected_csv_row(cd):
        return "{first_name},{last_name},{coach_cert},\"{niche_description}\",{website_url},{email},{instagram_url},{twitter_url},{linkedin_url},{source_url}\n\n".format(
            first_name=cd.first_name, last_name=cd.last_name, coach_cert=str(cd.coach_cert), niche_description=cd.niche_description,
            website_url=cd.website_url, email=cd.email, instagram_url=cd.instagram_url, twitter_url=cd.twitter_url,
            linkedin_url=cd.linkedin_url, source_url=cd.source_url
        )

    def setUp(self):
        if not logger.does_logger_exist():
            logger.initialize_logger(logger.Level.CRITICAL)

        if not config.is_config_loaded():
            config.load_config("config_dir/config.ini")

    def test_write_to_csv(self):
        global HEADER_ROW
        raw_data_1 = {
            "source_url": "coachdir.com/coach_one",
            "first_name": "Coach",
            "last_name": "One",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, One, Things",
            "website_url": "coachone.com",
            "email": "coach.one@coachone.com",
            "instagram_url": "coachone",
            "twitter_url": "coachone",
            "linkedin_url": "coachone"
        }

        raw_data_2 = {
            "source_url": "coachdir.com/coach_two",
            "first_name": "Coach",
            "last_name": "Two",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, Two, Things",
            "website_url": "coachtwo.com",
            "email": "coach.two@coachtwo.com",
            "instagram_url": "coachtwo",
            "twitter_url": "coachtwo",
            "linkedin_url": "coachtwo"
        }

        raw_data_3 = {
            "source_url": "coachdir.com/coach_three",
            "first_name": "Coach",
            "last_name": "Three",
            "coach_cert": CoachCert.MASTER,
            "niche_description": "Coach, Three, Things",
            "website_url": "coachthree.com",
            "email": "coach.three@coachthree.com",
            "instagram_url": "coachthree",
            "twitter_url": "coachthree",
            "linkedin_url": "coachthree"
        }

        cd1 = CoachData(**raw_data_1)
        cd2 = CoachData(**raw_data_2)
        cd3 = CoachData(**raw_data_3)

        csv_file_path = config.read("GENERAL", "TEST_CSV_FILE_PATH")

        write_coaches_to_csv([cd1, cd2, cd3], csv_file_path)

        expected_csv_data = ",".join(HEADER_ROW) + "\n\n" + \
        self.coach_data_to_expected_csv_row(cd1) + \
        self.coach_data_to_expected_csv_row(cd2) + \
        self.coach_data_to_expected_csv_row(cd3)

        with open(csv_file_path, 'r') as csv_file:
            csv_file_contents = csv_file.read()
            self.assertEqual(expected_csv_data, csv_file_contents)