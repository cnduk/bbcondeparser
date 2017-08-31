
import unittest

from bbcondeparser import (
    ErrorText,
    TagCategory,
    BaseHTMLRenderTreeParser,
    BaseHTMLTag,
    HtmlSimpleTag,
)


#
# Tag categories
#


INLINE_TAGS = TagCategory('Simple tags')
BASIC_TAGS = TagCategory('Basic tags')
BLOCK_TAGS = TagCategory('Block tags')
LIST_TAGS = TagCategory('List tags')
ALL_TAGS = TagCategory('All tags')


#
# Tags
#


class BoldTag(HtmlSimpleTag):
    tag_name = 'b'
    template = '<strong>{}</strong>'.format(HtmlSimpleTag.replace_text)
    tag_categories = [INLINE_TAGS, BASIC_TAGS, ALL_TAGS]
    allowed_tags = [INLINE_TAGS]


class ItalicTag(HtmlSimpleTag):
    tag_name = 'i'
    template = '<em>{}</em>'.format(HtmlSimpleTag.replace_text)
    tag_categories = [INLINE_TAGS, BASIC_TAGS, ALL_TAGS]
    allowed_tags = [INLINE_TAGS]


class ImageTag(BaseHTMLTag):
    tag_name = 'img'
    tag_display = 'block'
    self_closing = True
    attr_defs = {
        'src': {},
    }
    tag_categories = [BASIC_TAGS, BLOCK_TAGS, ALL_TAGS]

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
    tag_categories = [BLOCK_TAGS, ALL_TAGS]
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
    tag_categories = [BLOCK_TAGS, ALL_TAGS]

    def _render(self):
        return '<blockquote>{children}</blockquote>'.format(
            children=self.render_children(),
        )


class ChildSearcher(BaseHTMLTag):
    def find_children_instances(self, cls, multi=True):
        """This method searches immediate children for instances of `cls`
            if `multi` is truthy, then a list of found instances is returned.
            if `multi` is falsy, then only the last found instance is
                returned, and any extra instances found before hand are
                replaced with ErrorText.
                If no instance is found, `None` is returned.
        """
        items = [
            (index, child)
            for index, child in enumerate(self.tree)
            if isinstance(child, cls)
        ]

        if multi:
            return [child for _, child in items]

        if len(items) == 0:
            return None

        if len(items) > 1:
            # Too many, use `index` from `items` to find bad children,
            # and replace with ErrorText
            for index, child in items[:-1]:
                self.tree[index] = ErrorText(
                    child.render_raw(),
                    reason="Extra {} tag".format(child.tag_name)
                )

        # Return the last defined
        return items[-1][1]


class InfoBoxItemKey(HtmlSimpleTag):
    template = None
    tag_name = 'key'
    allowed_tags = [INLINE_TAGS]


class InfoBoxItemValue(HtmlSimpleTag):
    template = None
    tag_name = 'value'
    allowed_tags = [INLINE_TAGS]


class InfoBoxItem(ChildSearcher):
    tag_name = 'item'
    tag_display = 'block'
    allowed_tags = [InfoBoxItemKey, InfoBoxItemValue]

    def __init__(self, *args, **kwargs):
        super(InfoBoxItem, self).__init__(*args, **kwargs)

        key_inst = self.find_children_instances(InfoBoxItemKey, multi=False)
        if key_inst is None:
            self._key = '<NOKEY>'  # probably want to do something nicer?
        else:
            self._key = key_inst.render()

        val_inst = self.find_children_instances(InfoBoxItemValue, multi=False)
        if val_inst is None:
            self._val = '<NOVAL>'  # probably want to do something nicer?
        else:
            self._val = val_inst.render()

    def _render(self):
        return '<td>{}</td><td>{}</td>'.format(self._key, self._val)


class InfoBoxTitle(BaseHTMLTag):
    tag_name = 'title'
    tag_display = 'block'
    allowed_tags = [INLINE_TAGS]

    def _render(self):
        return self.render_title(self.render_children())

    @staticmethod
    def render_title(content):
        return '<td colspan="2">{}</td>'.format(content)


class InfoBox(ChildSearcher):
    tag_name = 'infobox'
    tag_display = 'block'
    tag_categories = [BLOCK_TAGS, ALL_TAGS]
    allowed_tags = [InfoBoxItem, InfoBoxTitle]

    def __init__(self, *args, **kwargs):
        super(InfoBox, self).__init__(*args, **kwargs)

        self._title_instance = self.find_children_instances(
            InfoBoxTitle, multi=False)

        self._item_instances = self.find_children_instances(
            InfoBoxItem, multi=True)

    def _render(self):
        if self._title_instance is None:
            title = InfoBoxTitle.render_title('<NOTITLE>')  # Probably do something nicer
        else:
            title = self._title_instance.render()

        body = ''.join(item.render() for item in self._item_instances)

        return '<table>{}{}</table>'.format(title, body)


class CodeTag(BaseHTMLTag):
    tag_name = 'code'
    tag_display = 'block'
    tag_categories = [BLOCK_TAGS, ALL_TAGS]

    def _render(self):
        return '<code><pre>' + self.render_children_raw() + '</code></pre>'


class DivTag(BaseHTMLTag):
    tag_name = 'div'
    tag_display = 'block'
    tag_categories = [ALL_TAGS]
    convert_newlines = True
    convert_paragraphs = True

    def _render(self):
        return '<div>{children}</div>'.format(children=self.render_children())


class DefaultParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]


class ParagraphParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True


class NewlineParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_newlines = True


class ParagraphNewlinesParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True
    convert_newlines = True


class StripNewlinesParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    strip_newlines = True


class StripNewlinesNotParagraphsParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True
    strip_newlines = True


###############################################################################
# Unit test classes doon 'ere!
###############################################################################

class BaseTesty(unittest.TestCase):
    def _testy(self, input_text, expected_output):
        parser = self.parser(input_text)
        result_output = parser.render()
        self.assertEqual(
            expected_output,
            result_output,
            "not equal:\n{}\n{}\ntree:\n{}".format(
                expected_output, result_output, parser.pretty_format()
            )
        )


class DefaultParserTesty(BaseTesty):
    parser = DefaultParser


class ParagraphParserTesty(BaseTesty):
    parser = ParagraphParser


class NewlineParserTesty(BaseTesty):
    parser = NewlineParser


class ParagraphNewlinesParserTesty(BaseTesty):
    parser = ParagraphNewlinesParser


class StripNewlinesParserTesty(BaseTesty):
    parser = StripNewlinesParser


class StripNewlinesNotParagraphsParserTesty(BaseTesty):
    parser = StripNewlinesNotParagraphsParser


#
# Tests
#


class TestBoldItalic(DefaultParserTesty):
    def test_BI(self):
        self._testy(
            "[b][i]Hello, world![/i][/b]",
            "<strong><em>Hello, world!</em></strong>",
        )


class TestInfobox(DefaultParserTesty):
    def test_infobox(self):
        self._testy(
            """[infobox]
                [title]a magical title[/title]
                [item]
                    [key]bananas[/key]
                    [value]yellow[/value]
                [/item]
                [item]
                    [value]red/green[/value]
                    [key]apples[/key]
                [/item]
            [/infobox]""",
            "<table>"
                '<td colspan="2">a magical title</td>'
                "<td>bananas</td><td>yellow</td>"
                "<td>apples</td><td>red/green</td>"
            "</table>",
        )


class TestCodeTag(DefaultParserTesty):
    def test_codetag(self):
        self._testy(
            "[code][b][i]Hello, world![/i][/b][/code]",
            "<code><pre>[b][i]Hello, world![/i][/b]</code></pre>",
        )


class TestDivTag(DefaultParserTesty):
    def test_divtag(self):
        self._testy(
            "example\n\n[div][b]bold[/b] word[/div]\n\nexample",
            "example\n\n<div><p><strong>bold</strong> word</p></div>\n\nexample",
        )

    def test_divtag_multi(self):
        self._testy(
            "example\n\n[div][b]bold[/b] word\n\nbutts[/div]\n\nexample",
            "example\n\n<div><p><strong>bold</strong> word</p><p>butts</p></div>\n\nexample",
        )

    def test_divtag_multi_newline(self):
        self._testy(
            "example\n\n[div][b]bold[/b] word\nbutts[/div]\n\nexample",
            "example\n\n<div><p><strong>bold</strong> word<br />butts</p></div>\n\nexample",
        )


class TestParagraphs(ParagraphParserTesty):

    def test_single_words(self):
        self._testy(
            "some words",
            "<p>some words</p>",
        )

    def test_multiple_words(self):
        self._testy(
            "some words\n\nspaced between\n\nparagraphs",
            "<p>some words</p><p>spaced between</p><p>paragraphs</p>",
        )

    def test_inline_single(self):
        self._testy(
            "[b]Inline[/b]",
            "<p><strong>Inline</strong></p>",
        )

    def test_inline_double(self):
        self._testy(
            "[b]Inline[/b]\n\n[i]Inline[/i]",
            "<p><strong>Inline</strong></p><p><em>Inline</em></p>",
        )

    def test_inline_single_newline(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<p><strong>Inline</strong>\n<em>Inline</em></p>",
        )

    def test_block_standalone(self):
        self._testy(
            '[img src="butts"]',
            '<img src="butts">',
        )

    def test_block_text(self):
        self._testy(
            'paragraph\n\n[img src="butts"]\n\nparagraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )

    def test_block_text_no_newlines(self):
        self._testy(
            'paragraph[img src="butts"]paragraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )


class TestNewlines(NewlineParserTesty):

    def test_single_words(self):
        self._testy(
            "some words",
            "some words",
        )

    def test_multiple_words(self):
        self._testy(
            "some words\n\nspaced between\nparagraphs",
            "some words<br /><br />spaced between<br />paragraphs",
        )

    def test_inline_single(self):
        self._testy(
            "[b]Inline[/b]",
            "<strong>Inline</strong>",
        )

    def test_inline_double(self):
        self._testy(
            "[b]Inline[/b]\n\n[i]Inline[/i]",
            "<strong>Inline</strong><br /><br /><em>Inline</em>",
        )

    def test_inline_single_newline(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<strong>Inline</strong><br /><em>Inline</em>",
        )

    def test_block_standalone(self):
        self._testy(
            '[img src="butts"]',
            '<img src="butts">',
        )

    def test_block_text(self):
        self._testy(
            'paragraph\n\n[img src="butts"]\n\nparagraph',
            'paragraph<br /><br /><img src="butts"><br /><br />paragraph',
        )

    def test_block_text_no_newlines(self):
        self._testy(
            'paragraph[img src="butts"]paragraph',
            'paragraph<img src="butts">paragraph',
        )


class TestParagraphsNewlines(ParagraphNewlinesParserTesty):

    def test_single_words(self):
        self._testy(
            "some words",
            "<p>some words</p>",
        )

    def test_multiple_words(self):
        self._testy(
            "some words\n\nspaced between\nparagraphs",
            "<p>some words</p><p>spaced between<br />paragraphs</p>",
        )

    def test_inline_single(self):
        self._testy(
            "[b]Inline[/b]",
            "<p><strong>Inline</strong></p>",
        )

    def test_inline_double(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<p><strong>Inline</strong><br /><em>Inline</em></p>",
        )

    def test_inline_single_newline(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<p><strong>Inline</strong><br /><em>Inline</em></p>",
        )

    def test_block_standalone(self):
        self._testy(
            '[img src="butts"]',
            '<img src="butts">',
        )

    def test_block_text(self):
        self._testy(
            'paragraph\n\n[img src="butts"]\n\nparagraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )

    def test_block_text_no_newlines(self):
        self._testy(
            'paragraph[img src="butts"]paragraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )

    def test_block_text_newline_after_block(self):
        self._testy(
            'paragraph[img src="butts"]\nparagraph',
            '<p>paragraph</p><img src="butts"><br /><p>paragraph</p>',
        )


class TestStripNewlines(StripNewlinesParserTesty):

    def test_single_words(self):
        self._testy(
            "some words",
            "some words",
        )

    def test_multiple_words(self):
        self._testy(
            "some words\n\nspaced between\nparagraphs",
            "some wordsspaced betweenparagraphs",
        )

    def test_inline_single(self):
        self._testy(
            "[b]Inline[/b]",
            "<strong>Inline</strong>",
        )

    def test_inline_double(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<strong>Inline</strong><em>Inline</em>",
        )

    def test_inline_single_newline(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<strong>Inline</strong><em>Inline</em>",
        )

    def test_block_standalone(self):
        self._testy(
            '[img src="butts"]',
            '<img src="butts">',
        )

    def test_block_text(self):
        self._testy(
            'paragraph\n\n[img src="butts"]\n\nparagraph',
            'paragraph<img src="butts">paragraph',
        )

    def test_block_text_no_newlines(self):
        self._testy(
            'paragraph[img src="butts"]paragraph',
            'paragraph<img src="butts">paragraph',
        )

    def test_block_text_newline_after_block(self):
        self._testy(
            'paragraph[img src="butts"]\nparagraph',
            'paragraph<img src="butts">paragraph',
        )


class TestStripNewlinesNotParagraphs(StripNewlinesNotParagraphsParserTesty):

    def test_single_words(self):
        self._testy(
            "some words",
            "<p>some words</p>",
        )

    def test_multiple_words(self):
        self._testy(
            "some words\n\nspaced between\nparagraphs",
            "<p>some words</p><p>spaced betweenparagraphs</p>",
        )

    def test_inline_single(self):
        self._testy(
            "[b]Inline[/b]",
            "<p><strong>Inline</strong></p>",
        )

    def test_inline_double(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<p><strong>Inline</strong><em>Inline</em></p>",
        )

    def test_inline_single_newline(self):
        self._testy(
            "[b]Inline[/b]\n[i]Inline[/i]",
            "<p><strong>Inline</strong><em>Inline</em></p>",
        )

    def test_block_standalone(self):
        self._testy(
            '[img src="butts"]',
            '<img src="butts">',
        )

    def test_block_text(self):
        self._testy(
            'paragraph\n\n[img src="butts"]\n\nparagraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )

    def test_block_text_no_newlines(self):
        self._testy(
            'paragraph[img src="butts"]paragraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )

    def test_block_text_newline_after_block(self):
        self._testy(
            'paragraph[img src="butts"]\nparagraph',
            '<p>paragraph</p><img src="butts"><p>paragraph</p>',
        )





JUICY_TEST_INPUT = """[b]Lorem ipsum dolor sit amet[/b], consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

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

JUICY_TEST_OUTPUT = """<p><strong>Lorem ipsum dolor sit amet</strong>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p><img src="#"><p><em>Lorem ipsum dolor sit amet</em>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p><ul>
<li>Item 1</li>
<li><strong>Item 2</strong></li>
<li>Item 3</li>
<li><img src="#"></li>
<li>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.<br />Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</li>
</ul><blockquote>Example blockquote words</blockquote><p><strong><em>Lorem ipsum dolor sit amet</em></strong>, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>"""


class TestBigOne(ParagraphParserTesty):
    def test_big_one(self):
        self._testy(JUICY_TEST_INPUT, JUICY_TEST_OUTPUT)
