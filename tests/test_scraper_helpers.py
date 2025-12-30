import unittest
from scraper_helpers import detect_visa_signals, normalize_location, filter_by_keywords


class TestScraperHelpers(unittest.TestCase):

    def test_detect_visa_signals(self):
        text = "We offer LMIA and visa sponsorship for the right candidate"
        hits, score = detect_visa_signals(text)
        self.assertIn('lmia', [h.lower() for h in hits])
        self.assertGreaterEqual(score, 1)

        text2 = "No mention here"
        hits2, score2 = detect_visa_signals(text2)
        self.assertEqual(score2, 0)

    def test_normalize_location(self):
        city, prov = normalize_location('Toronto, ON')
        self.assertEqual(city, 'Toronto')
        self.assertEqual(prov, 'ON')

        city2, prov2 = normalize_location('Remote')
        self.assertEqual(city2, 'Remote')
        self.assertEqual(prov2, '')

    def test_filter_by_keywords(self):
        entry = {'title': 'Senior Technical Program Manager', 'description': 'Leading security programs', 'company': 'X'}
        self.assertTrue(filter_by_keywords(entry, ['Program Manager', 'TPM']))

        entry2 = {'title': 'Junior Engineer', 'description': 'Nothing relevant', 'company': 'Y'}
        self.assertFalse(filter_by_keywords(entry2, ['Program Manager']))


if __name__ == '__main__':
    unittest.main()
