
import unittest

from bbcondeparser import (
    BaseTag, SimpleTag, ErrorText, TagCategory,
    BaseHTMLRenderTreeParser, BaseHTMLTag, HtmlSimpleTag,
)


#
# Tag categories
#
SIMPLE_TAGS = TagCategory('Simple tags')
BASIC_TAGS = TagCategory('Basic tags')
LIST_TAGS = TagCategory('List tags')
ALL_TAGS = TagCategory('All tags')

#
# Tags
#


class BoldTag(HtmlSimpleTag):
    tag_name = 'b'
    template = '<strong>{}</strong>'.format(SimpleTag.replace_text)
    tag_categories = [SIMPLE_TAGS, BASIC_TAGS, ALL_TAGS]


class ItalicTag(HtmlSimpleTag):
    tag_name = 'i'
    template = '<em>{}</em>'.format(SimpleTag.replace_text)
    tag_categories = [SIMPLE_TAGS, BASIC_TAGS, ALL_TAGS]


class ImageTag(BaseHTMLTag):
    tag_name = 'img'
    tag_display = 'block'
    self_closing = True
    attr_defs = {
        'src': {},
    }
    tag_categories = [BASIC_TAGS, ALL_TAGS]

    def _render(self):
        return '<img src="{}">'.format(self.attrs['src'])


class ListTag(BaseHTMLTag):
    tag_name = 'list'
    tag_display = 'block'
    attr_defs = {
        'type': {
            'default': 'unordered',
        },
    }
    tag_categories = [ALL_TAGS]
    allowed_tags = [LIST_TAGS]

    def _render(self):

        tag_type = 'ul'
        if self.attrs['type'] == 'ordered':
            tag_type = 'ol'

        return '<{tag_type}>{children}</{tag_type}>'.format(
            tag_type=tag_type,
            children=self.render_children(),
        )


class ListItemTag(BaseHTMLTag):
    tag_name = 'item'
    tag_display = 'block'
    tag_categories = [LIST_TAGS]
    allowed_tags = [BASIC_TAGS]
    convert_newlines = True

    def _render(self):
        return '<li>{children}</li>'.format(
            children=self.render_children(),
        )


class BlockquoteTag(BaseHTMLTag):
    tag_name = 'blockquote'
    tag_display = 'block'
    tag_categories = [ALL_TAGS]

    def _render(self):
        return '<blockquote>{children}</blockquote>'.format(
            children=self.render_children(),
        )


class Parser(BaseHTMLRenderTreeParser):
    tags = [ALL_TAGS]
    convert_paragraphs = True
    # convert_newlines = True


###############################################################################
# Unit test classes doon 'ere!
###############################################################################

class BaseTesty(unittest.TestCase):

    parser = Parser

    def _testy(self, input_text, expected_output):
        parser = self.parser(input_text)
        result_output = parser.render()
        self.assertEqual(
            expected_output,
            result_output,
            "not equal:\n{}\n-\n{}\n-\ntree:\n{}".format(
                expected_output, result_output, parser.pretty_format()
            )
        )


JUICE_TEST_INPUT = """[b]Lorem ipsum dolor sit amet[/b], consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

[img src='#']

[i]Lorem ipsum dolor sit amet[/i], consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

[list]
[item]Item 1[/item]
[item][b]Item 2[/b][/item]
[item]Item 3[/item]
[item][img src='#'][/item]
[item]Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[/item]
[/list]

[blockquote]Example blockquote words[/blockquote]

[b][i]Lorem ipsum dolor sit amet[/i][/b], consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

JUICE_TEST_OUTPUT = """<p><strong>Lorem ipsum dolor sit amet</strong>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p><img src="#"><p><em>Lorem ipsum dolor sit amet</em>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p><ul>
<li>Item 1</li>
<li><strong>Item 2</strong></li>
<li>Item 3</li>
<li><img src="#"></li>
<li>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.<br />Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</li>
</ul><blockquote>Example blockquote words</blockquote><p><strong><em>Lorem ipsum dolor sit amet</em></strong>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>"""


class JuicyTest(BaseTesty):
    def test_big_one(self):
        self._testy(JUICE_TEST_INPUT, JUICE_TEST_OUTPUT)
