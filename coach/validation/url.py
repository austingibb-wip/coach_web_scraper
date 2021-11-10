import re
from unittest import TestCase

from coach.validation.general import validate_default

url_regex = re.compile(
    r"^(?:(?:http|ftp)s?://)?"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def validate_url(url):
    match = re.match(url_regex, url) is not None
    return match


def validate_url_or_default(url, default=""):
    return validate_default(validate_url, url, default)


class _UrlValidatorTest(TestCase):
    def test_http(self):
        url = "http://google.com"
        self.assertEqual(validate_url(url), True)

    def test_www(self):
        url = "http://www.yourmom.com"
        self.assertEqual(validate_url(url), True)

    def test_no_http(self):
        url = "hi.com"
        self.assertEqual(validate_url(url), True)

    def test_subdomain(self):
        url = "hi.there.com"
        self.assertEqual(validate_url(url), True)

    def test_subdomain_resource(self):
        url = "hi.there.com/specific_resource?sfjdd=8&fddd=2"
        self.assertEqual(validate_url(url), True)

    def test_reject_whitespace(self):
        url = "hi.com/ rejected"
        self.assertEqual(validate_url(url), False)

    def test_non_url(self):
        url = "notawebsite/hello"
        self.assertEqual(validate_url(url), False)
