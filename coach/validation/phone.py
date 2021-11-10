import re
from unittest import TestCase

from coach.validation.general import validate_default

phone_regex = re.compile("^1?([0-9]{3})?[0-9]{7}$")


def normalize_phone(phone: str) -> str:
    translation_table = dict.fromkeys(map(ord, "+.-() \t"), None)
    return phone.translate(translation_table)


def validate_phone(phone):
    phone = normalize_phone(phone)
    match = re.match(phone_regex, phone) is not None
    return match


def validate_phone_or_default(phone, default=""):
    return validate_default(validate_phone, phone, default)


class _PhoneValidatorTest(TestCase):
    def test_phone(self):
        phone = "+1 (801).888.8888"
        self.assertEqual(validate_phone(phone), True)

    def test_notphone(self):
        phone = "888 888 8888 hi"
        self.assertEqual(validate_phone(phone), False)


class _NormalizePhoneTest(TestCase):
    def test_phone_with_parenthesis(self):
        self.assertEqual(normalize_phone("(385) 999 1233"), "3859991233")

    def test_phone_with_dashes(self):
        self.assertEqual(normalize_phone("123-456-7890"), "1234567890")

    def test_phone_with_country_code(self):
        self.assertEqual(normalize_phone("+1 123-456-7890"), "11234567890")
