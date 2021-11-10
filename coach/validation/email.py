from unittest import TestCase

import validators

from coach.validation.general import validate_default


def validate_email(email):
    result = validators.email(email)
    if isinstance(result, validators.ValidationFailure):
        result = False
    return result


def validate_email_or_default(email, default=""):
    return validate_default(validate_email, email, default)


class _EmailValidatorTest(TestCase):
    def test_email(self):
        email = "myname.jeff@gmail.com"
        self.assertEqual(validate_email(email), True)

    def test_nonemail(self):
        email = "notanemail.com"
        self.assertEqual(validate_email(email), False)
