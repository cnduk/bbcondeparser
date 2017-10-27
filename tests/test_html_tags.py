
import unittest

from bbcondeparser import html_tags


class TestBaseHTMLTagMeta(unittest.TestCase):

    def test_newline_runtime_error(self):
        with self.assertRaises(RuntimeError):
            class BadTag(html_tags.BaseHTMLTag):
                tag_name = 'bad_tag'
                newline_behaviour = 'butts'
