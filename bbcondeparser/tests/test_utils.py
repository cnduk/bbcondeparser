import unittest

from bbcondeparser import utils

class TextBackslashEscape(unittest.TestCase):
    def test_escape(self):
        input = r'\1\2\\\"'
        expected = r'12\"'

        result = utils.remove_backslash_escapes(input)

        self.assertEqual(expected, result)


class TextNewline(unittest.TestCase):
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

    def test_convert_default(self):
        input = 'example\n newline'
        expected = 'example<br /> newline'

        result = utils.convert_newlines(input)

        self.assertEqual(expected, result)

    def test_convert_custom(self):
        input = 'example\n newline'
        expected = 'examplebutts newline'
        result = utils.convert_newlines(input, convert_char='butts')
        self.assertEqual(expected, result)

        input = 'examplebig newline'
        expected = 'examplebutts newline'
        result = utils.convert_newlines(input, 'big', 'butts')
        self.assertEqual(expected, result)


    def test_normalize(self):
        # No newlines
        input = 'example newline'
        expected = 'example newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)

        # \n => \n
        input = 'example newline'
        expected = 'example newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)

        # \r\n => \n
        input = 'example\r\n newline'
        expected = 'example\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)

        # \n\n\n\n => \n\n
        input = 'example\n\n\n\n newline'
        expected = 'example\n\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)

        # \r\n\n\r\n => \n\n
        input = 'example\r\n\n\r\n newline'
        expected = 'example\n\n newline'
        result = utils.normalize_newlines(input)
        self.assertEqual(expected, result)
