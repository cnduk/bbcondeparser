import unittest

from bbcondeparser import utils

class TextBackslashEscape(unittest.TestCase):
    def test_escape(self):
        input = r'\1\2\\\"'
        expected = r'12\"'

        result = utils.remove_backslash_escapes(input)

        self.assertEqual(expected, result)


class TextNewlineStrip(unittest.TestCase):
    def test_strip_default(self):
        input = 'example\n newline'
        expected = 'example newline'

        result = utils.strip_newlines(input)

        self.assertEqual(expected, result)


    def test_strip_custom(self):
        input = 'examplebutts newline'
        expected = 'example newline'

        result = utils.strip_newlines(input, 'butts')

        self.assertEqual(expected, result)


class TextNewlineConvert(unittest.TestCase):
    def test_convert_default(self):
        input = 'example\n newline'
        expected = 'example<br /> newline'

        result = utils.convert_newlines(input)

        self.assertEqual(expected, result)


    def test_convert_custom_convert_char(self):
        input = 'example\n newline'
        expected = 'examplebutts newline'

        result = utils.convert_newlines(input, convert_char='butts')

        self.assertEqual(expected, result)


    def test_convert_custom_convert_char_and_replace(self):
        input = 'examplebig newline'
        expected = 'examplebutts newline'

        result = utils.convert_newlines(input, 'big', 'butts')

        self.assertEqual(expected, result)


class TextNewline(unittest.TestCase):

    def test_normalize_none(self):
        # No newlines
        input = 'example newline'
        expected = 'example newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)


    def test_normalize_single(self):
        # \n => \n
        input = 'example newline'
        expected = 'example newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)


    def test_normalize_return(self):
        # \r\n => \n
        input = 'example\r\n newline'
        expected = 'example\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)


    def test_normalize_double_double(self):
        # \n\n\n\n => \n\n
        input = 'example\n\n\n\n newline'
        expected = 'example\n\n\n\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)


    def test_normalize_wat(self):
        # \r\n\n\r\n => \n\n\n
        input = 'example\r\n\n\r\n newline'
        expected = 'example\n\n\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)
