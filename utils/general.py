from unittest import TestCase


def affix_variations(prefix):
    """
    e.g.
    dr -> ["dr", "dr.", "d.r.", "d.r"]
    phd -> ["phd", "phd.", "ph.d", "ph.d.", "p.hd", "p.hd.", "p.h.d", "p.h.d."]
    :param prefix: string to expand into acronym w/ different punctuation
    :return: variations of acronym as set
    """
    variations = set()

    for power_set_index in range(0, 2 ** len(prefix)):
        variation = ""
        # get binary string representation of power_set_index zero padded to length of prefix
        bin_i = ("{0:0" + str(len(prefix)) + "b}").format(power_set_index)
        for index, char in enumerate(prefix):
            variation += char + ("." if bin_i[index] == "1" else "")
        variations.add(variation)

    return variations


class _AffixVariation(TestCase):
    def test_affix_variation(self):
        self.assertEqual({"dr", "dr.", "d.r", "d.r."}, affix_variations("dr"))

    def test_affix_variation_larger(self):
        self.assertEqual(
            {"phd", "phd.", "ph.d", "ph.d.", "p.hd", "p.hd.", "p.h.d", "p.h.d."},
            affix_variations("phd"),
        )
