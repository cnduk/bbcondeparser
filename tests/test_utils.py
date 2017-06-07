import unittest

from bbcondeparser import utils

class TextBackslashEscape(unittest.TestCase):
    def test_escape(self):
        input_text = r'\1\2\\\"'
        expected = r'12\"'

        result = utils.remove_backslash_escapes(input_text)

        self.assertEqual(expected, result)
