import re
from unittest import TestCase

from coach.validation.general import validate_default

social_media_handle_regex = re.compile("^\s*(@?[A-Za-z0-9-_]+(?![@]))\s*$")


def validate_handle(handle):
    match = re.match(social_media_handle_regex, handle) is not None
    return match


def validate_handle_or_default(handle, default=""):
    return validate_default(validate_handle, handle, default)


class _HandleValidatorTest(TestCase):
    def test_handle_no_at(self):
        handle = "somehandle"
        self.assertEqual(validate_handle(handle), True)

    def test_handle_with_at(self):
        handle = "@twitteruser"
        self.assertEqual(validate_handle(handle), True)

    def test_handle_reject_email(self):
        handle = "not_a_handle@gmail.com"
        self.assertEqual(validate_handle(handle), False)

    def test_handle_reject_url(self):
        handle = "website.com"
        self.assertEqual(validate_handle(handle), False)
