import unittest

from bbcondeparser import utils

class TextBackslashEscape(unittest.TestCase):
    def test_escape(self):
        input_text = r'\1\2\\\"'
        expected = r'12\"'

        result = utils.remove_backslash_escapes(input_text)

        self.assertEqual(expected, result)


class TextNewlineStrip(unittest.TestCase):
    def test_strip_default(self):
        input_text = 'example\n newline'
        expected = 'example newline'

        result = utils.strip_newlines(input_text)

        self.assertEqual(expected, result)


    def test_strip_custom(self):
        input_text = 'examplebutts newline'
        expected = 'example newline'

        result = utils.strip_newlines(input_text, 'butts')

        self.assertEqual(expected, result)


class TextNewlineConvert(unittest.TestCase):
    def test_convert_default(self):
        input_text = 'example\n newline'
        expected = 'example<br /> newline'

        result = utils.convert_newlines(input_text)

        self.assertEqual(expected, result)


    def test_convert_custom_convert_char(self):
        input_text = 'example\n newline'
        expected = 'examplebutts newline'

        result = utils.convert_newlines(input_text, convert_char='butts')

        self.assertEqual(expected, result)


    def test_convert_custom_convert_char_and_replace(self):
        input_text = 'examplebig newline'
        expected = 'examplebutts newline'

        result = utils.convert_newlines(input_text, 'big', 'butts')

        self.assertEqual(expected, result)