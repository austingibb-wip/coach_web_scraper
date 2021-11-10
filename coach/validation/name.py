from unittest import TestCase

from utils.general import affix_variations

_all_affixes = set()


def init_all_affixes():
    global _all_affixes
    for affix in [
        "dr",
        "mba",
        "ma",
        "md",
        "ra",
        "phd",
        "rn",
        "msa",
        "pcc",
        "mr",
        "ms",
        "mrs",
    ]:
        _all_affixes = _all_affixes.union(affix_variations(affix))


def normalize_name(name):
    name_tokens = [nt.lower().capitalize() for nt in name.split()]
    return " ".join(name_tokens)


def extract_name(name_text):
    global _all_affixes
    if len(_all_affixes) == 0:
        init_all_affixes()

    name_tokens = name_text.split(",")[0].split()
    filtered_tokens = []
    for token in name_tokens:
        # lowercase token to simplify
        token = token.lower()

        if token in _all_affixes:
            continue
        filtered_tokens.append(token)

    if len(filtered_tokens) < 2:
        return "", ""
    elif len(filtered_tokens) == 3:
        return filtered_tokens[0], filtered_tokens[2]
    elif len(filtered_tokens) >= 2:
        return filtered_tokens[0], filtered_tokens[1]


class _ExtractName(TestCase):
    def test_remove_prefix(self):
        first, last = extract_name("Dr. Jeremy Long")
        self.assertEqual("jeremy", first)
        self.assertEqual("long", last)

    def test_long_name(self):
        first, last = extract_name("jacob j more")
        self.assertEqual("jacob", first)
        self.assertEqual("more", last)

    def test_insufficient_name(self):
        first, last = extract_name("jacob phd")
        self.assertEqual("", first)
        self.assertEqual("", last)

    def test_missed_suffix_name(self):
        first, last = extract_name("jacob more ijh jkl")
        self.assertEqual("jacob", first)
        self.assertEqual("more", last)
