import unittest

from bbcondeparser import (
    BaseTag, SimpleTag, ErrorText, BaseTreeParser, TagCategory
)

###############################################################################
# Definition of tags and parsers up here
###############################################################################

SIMPLE_TAGS = TagCategory("simple tags")

class Bold(SimpleTag):
    tag_name = 'b'
    template = '<b>{}</b>'.format(SimpleTag.replace_text)
    tag_categories = [SIMPLE_TAGS]

class Italic(SimpleTag):
    tag_name = 'i'
    template = '<i>{}</i>'.format(SimpleTag.replace_text)
    tag_categories = [SIMPLE_TAGS]

class Image(BaseTag):
    tag_name = 'img'
    self_closing = True

    attr_defs = {
        'src': {} # required, no parser.
    }

    def _render(self):
        return '<img src="{}">'.format(self.attrs['src'])


class ChildSearcher(BaseTag):
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


class InfoBoxItemKey(SimpleTag):
    template = None
    tag_name = 'key'
    allowed_tags = [SIMPLE_TAGS]


class InfoBoxItemValue(SimpleTag):
    template = None
    tag_name = 'value'
    allowed_tags = [SIMPLE_TAGS]


class InfoBoxItem(ChildSearcher):
    tag_name = 'item'
    allowed_tags = [InfoBoxItemKey, InfoBoxItemValue]

    def __init__(self, *args, **kwargs):
        super(InfoBoxItem, self).__init__(*args, **kwargs)

        key_inst = self.find_children_instances(InfoBoxItemKey, multi=False)
        if key_inst is None:
            self._key = '<NOKEY>' # probably want to do something nicer?
        else:
            self._key = key_inst.render()

        val_inst = self.find_children_instances(InfoBoxItemValue, multi=False)
        if val_inst is None:
            self._val = '<NOVAL>' # probably want to do something nicer?
        else:
            self._val = val_inst.render()

    def _render(self):
        return '<td>{}</td><td>{}</td>'.format(self._key, self._val)


class InfoBoxTitle(BaseTag):
    tag_name = 'title'
    allowed_tags = [SIMPLE_TAGS]

    def _render(self):
        return self.render_title(self.render_children())

    @staticmethod
    def render_title(content):
        return '<td colspan="2">{}</td>'.format(content)


class InfoBox(ChildSearcher):
    tag_name = 'infobox'
    allowed_tags = [InfoBoxItem, InfoBoxTitle]

    def __init__(self, *args, **kwargs):
        super(InfoBox, self).__init__(*args, **kwargs)

        self._title_instance = self.find_children_instances(
                InfoBoxTitle, multi=False)

        self._item_instances = self.find_children_instances(
                InfoBoxItem, multi=True)

    def _render(self):
        if self._title_instance is None:
            title = InfoBoxTitle.render_title('<NOTITLE>') # Probably do something nicer
        else:
            title = self._title_instance.render()

        body = ''.join(item.render() for item in self._item_instances)

        return '<table>{}{}</table>'.format(title, body)


class CodeTag(BaseTag):
    tag_name = 'code'
    def _render(self):
        return '<code><pre>' + self.render_children_raw() + '</code></pre>'


class NoParagraphsTag(BaseTag):
    tag_name = 'nope'

    def _render(self):
        return self.render_children()


class ParagraphsTag(BaseTag):
    tag_name = 'p'
    convert_paragraphs = True

    def _render(self):
        return self.render_children()


class ParagraphsTagWithLineBreaks(BaseTag):
    tag_name = 'pp'
    convert_paragraphs = True
    convert_newlines = True

    def _render(self):
        return self.render_children()


class Parser(BaseTreeParser):
    tags = [SIMPLE_TAGS, InfoBox, CodeTag, NoParagraphsTag, ParagraphsTag,
        ParagraphsTagWithLineBreaks]
    ignored_tags = [Image]


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
            "not equal:\n{}\n{}\ntree:\n{}".format(
                expected_output, result_output, parser.pretty_format()
            )
        )

class TestBoldItalic(BaseTesty):
    def test_BI(self):
        self._testy(
            "[b][i]Hello, world![/i][/b]",
            "<b><i>Hello, world!</i></b>",
        )


class TestInfobox(BaseTesty):
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


class TestIgnored(BaseTesty):
    def test_ignored(self):
        self._testy(
            '[img src="dontrenderme"]hello!',
            "hello!",
        )


class TestCodeTag(BaseTesty):
    def test_codetag(self):
        self._testy(
            "[code][b][i]Hello, world![/i][/b][/code]",
            "<code><pre>[b][i]Hello, world![/i][/b]</code></pre>",
        )


class TestTagRenderParagraphs(BaseTesty):
    def test_render_simple(self):
        self._testy(
            '[p]example 1\n\nexample 2[/p]',
            '<p>example 1</p><p>example 2</p>'
        )

    def test_render_multiple(self):
        self._testy(
            '[p]example 1\n\nexample 2\nexample 3\n\nexample 4\n[/p]',
            '<p>example 1</p><p>example 2\nexample 3</p><p>example 4\n</p>'
        )

    def test_render_inline(self):
        self._testy(
            '[p]example 1\n\nexample 2\nexample 3\n\n[b]example 4[/b]\n[/p]',
            '<p>example 1</p><p>example 2\nexample 3</p><p><b>example 4</b>\n</p>'
        )


class TestTagRenderParagraphsLineBreaks(BaseTesty):
    def test_render_simple(self):
        self._testy(
            '[pp]example 1\n\nexample 2[/pp]',
            '<p>example 1</p><p>example 2</p>'
        )

    def test_render_multiple(self):
        self._testy(
            '[pp]example 1\n\nexample 2\nexample 3\n\nexample 4\n[/pp]',
            '<p>example 1</p><p>example 2<br />example 3</p><p>example 4<br /></p>'
        )

    def test_render_inline(self):
        self._testy(
            '[pp]example 1\n\nexample 2\nexample 3\n\n[b]example 4[/b]\n[/pp]',
            '<p>example 1</p><p>example 2<br />example 3</p><p><b>example 4</b><br /></p>'
        )


class TestTagRenderParagraphsAndNone(BaseTesty):
    def test_render_simple(self):
        self._testy(
            '[p]example 1\n\n[nope]example 2\n\nexample 3[/nope]\n\nexample 4[/p]',
            '<p>example 1</p><p>example 2\n\nexample 3</p><p>example 4</p>'
        )

    def test_render_multiple(self):
        self._testy(
            '[p]example 1\n\n[nope]example 2\n\nexample 3\n\n[p]example 5\n\nexample 6[/p][/nope]\n\nexample 4[/p]',
            '<p>example 1</p><p>example 2\n\nexample 3\n\n<p>example 5</p><p>example 6</p></p><p>example 4</p>'
        )
