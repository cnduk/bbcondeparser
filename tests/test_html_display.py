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


INLINE_TAGS = TagCategory("Simple tags")
BASIC_TAGS = TagCategory("Basic tags")
BLOCK_TAGS = TagCategory("Block tags")
LIST_TAGS = TagCategory("List tags")
ALL_TAGS = TagCategory("All tags")


#
# Tags
#


class BoldTag(HtmlSimpleTag):
    tag_name = "b"
    template = "<strong>{}</strong>".format(HtmlSimpleTag.replace_text)
    tag_categories = [INLINE_TAGS, BASIC_TAGS, ALL_TAGS]
    allowed_tags = [INLINE_TAGS]
    newline_behaviour = "convert"


class ItalicTag(HtmlSimpleTag):
    tag_name = "i"
    template = "<em>{}</em>".format(HtmlSimpleTag.replace_text)
    tag_categories = [INLINE_TAGS, BASIC_TAGS, ALL_TAGS]
    allowed_tags = [INLINE_TAGS]
    newline_behaviour = "convert"


class ImageTag(BaseHTMLTag):
    tag_name = "img"
    tag_display = "block"
    self_closing = True
    attr_defs = {
        "src": {},
    }
    tag_categories = [BASIC_TAGS, BLOCK_TAGS, ALL_TAGS]

    def _render(self, **kwargs):
        return '<img src="{}">'.format(self.attrs["src"])


class ListTag(BaseHTMLTag):
    tag_name = "list"
    tag_display = "block"
    attr_defs = {
        "type": {"default": "unordered",},
    }
    tag_categories = [BLOCK_TAGS, ALL_TAGS]
    allowed_tags = [LIST_TAGS]

    def _render(self):

        tag_type = "ul"
        if self.attrs["type"] == "ordered":
            tag_type = "ol"

        return "<{tag_type}>{children}</{tag_type}>".format(
            tag_type=tag_type, children=self.render_children(),
        )


class ListItemTag(BaseHTMLTag):
    tag_name = "item"
    tag_display = "block"
    tag_categories = [LIST_TAGS]
    allowed_tags = [BASIC_TAGS]
    newline_behaviour = "convert"

    def _render(self):
        return "<li>{children}</li>".format(children=self.render_children(),)


class BlockquoteTag(BaseHTMLTag):
    tag_name = "blockquote"
    tag_display = "block"
    tag_categories = [BLOCK_TAGS, ALL_TAGS]

    def _render(self):
        return "<blockquote>{children}</blockquote>".format(
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
                    child.render_raw(), reason="Extra {} tag".format(child.tag_name)
                )

        # Return the last defined
        return items[-1][1]


class InfoBoxItemKey(HtmlSimpleTag):
    template = None
    tag_name = "key"
    allowed_tags = [INLINE_TAGS]


class InfoBoxItemValue(HtmlSimpleTag):
    template = None
    tag_name = "value"
    allowed_tags = [INLINE_TAGS]


class InfoBoxItem(ChildSearcher):
    tag_name = "item"
    tag_display = "block"
    allowed_tags = [InfoBoxItemKey, InfoBoxItemValue]

    def __init__(self, *args, **kwargs):
        super(InfoBoxItem, self).__init__(*args, **kwargs)

        key_inst = self.find_children_instances(InfoBoxItemKey, multi=False)
        if key_inst is None:
            self._key = "<NOKEY>"  # probably want to do something nicer?
        else:
            self._key = key_inst.render()

        val_inst = self.find_children_instances(InfoBoxItemValue, multi=False)
        if val_inst is None:
            self._val = "<NOVAL>"  # probably want to do something nicer?
        else:
            self._val = val_inst.render()

    def _render(self, **kwargs):
        return "<td>{}</td><td>{}</td>".format(self._key, self._val)


class InfoBoxTitle(BaseHTMLTag):
    tag_name = "title"
    tag_display = "block"
    allowed_tags = [INLINE_TAGS]

    def _render(self):
        return self.render_title(self.render_children())

    @staticmethod
    def render_title(content):
        return '<td colspan="2">{}</td>'.format(content)


class InfoBox(ChildSearcher):
    tag_name = "infobox"
    tag_display = "block"
    tag_categories = [BLOCK_TAGS, ALL_TAGS]
    allowed_tags = [InfoBoxItem, InfoBoxTitle]

    def __init__(self, *args, **kwargs):
        super(InfoBox, self).__init__(*args, **kwargs)

        self._title_instance = self.find_children_instances(InfoBoxTitle, multi=False)

        self._item_instances = self.find_children_instances(InfoBoxItem, multi=True)

    def _render(self):
        if self._title_instance is None:
            title = InfoBoxTitle.render_title(
                "<NOTITLE>"
            )  # Probably do something nicer
        else:
            title = self._title_instance.render()

        body = "".join(item.render() for item in self._item_instances)

        return "<table>{}{}</table>".format(title, body)


class CodeTag(BaseHTMLTag):
    tag_name = "code"
    tag_display = "block"
    tag_categories = [BLOCK_TAGS, ALL_TAGS]

    def _render(self):
        return "<code><pre>" + self.render_children_raw() + "</code></pre>"


class DivTag(BaseHTMLTag):
    tag_name = "div"
    tag_display = "block"
    tag_categories = [ALL_TAGS]
    convert_paragraphs = True
    newline_behaviour = "convert"

    def _render(self):
        return "<div>{children}</div>".format(children=self.render_children())


class BaseDivTag(BaseHTMLTag):
    tag_display = "block"
    tag_categories = [ALL_TAGS]

    def _render(self):
        return "<div>{children}</div>".format(children=self.render_children())


class NewlineTrueTag(BaseDivTag):
    tag_name = "newline-true"
    newline_behaviour = "convert"


class NewlineFalseTag(BaseDivTag):
    tag_name = "newline-false"
    newline_behaviour = "ignore"


class NewlineInheritTag(BaseDivTag):
    tag_name = "newline-inherit"


class ParagraphTrueTag(BaseDivTag):
    tag_name = "paragraph-true"
    convert_paragraphs = True


class ParagraphFalseTag(BaseDivTag):
    tag_name = "paragraph-false"
    convert_paragraphs = False


class ParagraphInheritTag(BaseDivTag):
    tag_name = "paragraph-inherit"


class StripNewlinesTrueTag(BaseDivTag):
    tag_name = "stripnewlines-true"
    newline_behaviour = "remove"


class StripNewlinesFalseTag(BaseDivTag):
    tag_name = "stripnewlines-false"
    newline_behaviour = "ignore"


class StripNewlinesInheritTag(BaseDivTag):
    tag_name = "stripnewlines-inherit"


class DefaultParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    newline_behaviour = "ignore"


class ParagraphParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True


class NewlineParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    newline_behaviour = "convert"


class ParagraphNewlinesParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True
    newline_behaviour = "convert"


class StripNewlinesParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    newline_behaviour = "remove"


class StripNewlinesNotParagraphsParser(BaseHTMLRenderTreeParser):
    tags = [
        ALL_TAGS,
    ]
    convert_paragraphs = True
    newline_behaviour = "remove"


class RenderSelectedTagsParser(BaseHTMLRenderTreeParser):
    tags = [
        INLINE_TAGS,
    ]


###############################################################################
# Unit test classes doon 'ere!
###############################################################################


class BaseTest(unittest.TestCase):
    def _run_tests(self, baseparser, input_text, expected_output):
        parser = baseparser(input_text)
        rendered_output = parser.render(getattr(parser, "render_context", None))
        self.assertEqual(
            expected_output,
            rendered_output,
            "NOT EQUAL!\nExpected:\n{expected}\n---\nActual:\n{actual}\n---\ntree:\n{tree}".format(
                expected=expected_output,
                actual=rendered_output,
                tree=parser.pretty_format(),
            ),
        )


class InlineTagTests(BaseTest):
    def test_render(self):
        self._run_tests(
            DefaultParser, "[b]bold tag[/b]", "<strong>bold tag</strong>",
        )

    def test_render_other_inline(self):
        self._run_tests(
            DefaultParser,
            "[b]bold[/b] and [i]italic[/i] tag",
            "<strong>bold</strong> and <em>italic</em> tag",
        )

    def test_dont_render_blocks(self):
        self._run_tests(
            DefaultParser,
            "[b]bold cant render [div]div[/div] tags[/b]",
            "<strong>bold cant render div tags</strong>",
        )


class BlockTagTests(BaseTest):
    def test_render(self):
        self._run_tests(
            DefaultParser,
            "text outside [div]text inside[/div] text outside",
            "text outside <div><p>text inside</p></div> text outside",
        )

    def test_render_inline(self):
        self._run_tests(
            DefaultParser,
            "text outside [div][b]text[/b]\n[i]inside[/i][/div] text outside",
            "text outside <div><p><strong>text</strong>\n<em>inside</em></p></div> text outside",
        )

    def test_render_blocks(self):
        self._run_tests(
            DefaultParser,
            "text outside [div]with another [div]div inside[/div][/div] text outside",
            "text outside <div><p>with another </p><div><p>div inside</p></div></div> text outside",
        )


class NewlineTests(BaseTest):
    def test_none(self):
        self._run_tests(
            NewlineParser, "no newlines in this copy", "no newlines in this copy",
        )

    def test_single(self):
        self._run_tests(
            NewlineParser,
            "there is one single\nnewline in this copy",
            "there is one single<br />newline in this copy",
        )

    """
    Multiple \n should only ever return a single <br />
    """

    def test_double(self):
        self._run_tests(
            NewlineParser,
            "there is two single\n\nnewline in this copy",
            "there is two single<br />newline in this copy",
        )

    def test_triple(self):
        self._run_tests(
            NewlineParser,
            "there is three single\n\n\nnewline in this copy",
            "there is three single<br />newline in this copy",
        )

    def test_true(self):
        self._run_tests(
            NewlineParser,
            "copy here [newline-true]a newline\nin this copy[/newline-true] copy here",
            "copy here <div>a newline<br />in this copy</div> copy here",
        )

    def test_false(self):
        self._run_tests(
            NewlineParser,
            "copy here [newline-false]a newline\nin this copy[/newline-false] copy here",
            "copy here <div>a newline\nin this copy</div> copy here",
        )

    def test_inherit(self):
        self._run_tests(
            NewlineParser,
            "copy here [newline-inherit]a newline\nin this copy[/newline-inherit] copy here",
            "copy here <div>a newline<br />in this copy</div> copy here",
        )

    def test_inherit_deeper(self):
        self._run_tests(
            NewlineParser,
            "copy here [newline-inherit]newline\n[newline-false][newline-inherit]no\nnewline[/newline-inherit][/newline-false][/newline-inherit] copy here",
            "copy here <div>newline<br /><div><div>no\nnewline</div></div></div> copy here",
        )


class ParagraphTests(BaseTest):
    def test_none(self):
        self._run_tests(
            ParagraphParser, "", "",
        )

    def test_single(self):
        self._run_tests(
            ParagraphParser,
            "paragraph around this copy",
            "<p>paragraph around this copy</p>",
        )

    def test_double(self):
        self._run_tests(
            ParagraphParser,
            "there is a paragraph here\n\nthere is a paragraph here",
            "<p>there is a paragraph here</p><p>there is a paragraph here</p>",
        )

    def test_inline(self):
        self._run_tests(
            ParagraphParser,
            "[b]bold text[/b]\n\n[b]more bold text[/b]",
            "<p><strong>bold text</strong></p><p><strong>more bold text</strong></p>",
        )

    def test_block(self):
        self._run_tests(
            ParagraphParser,
            "[div]a block is here[/div]some text is here[div]a block is here[/div]some text is here",
            "<div><p>a block is here</p></div><p>some text is here</p><div><p>a block is here</p></div><p>some text is here</p>",
        )

    def test_true(self):
        self._run_tests(
            ParagraphParser,
            "copy here [paragraph-true]wrapped in paragraphs\n\nwrapped in paragraphs[/paragraph-true] copy here",
            "<p>copy here </p><div><p>wrapped in paragraphs</p><p>wrapped in paragraphs</p></div><p> copy here</p>",
        )

    def test_false(self):
        self._run_tests(
            ParagraphParser,
            "copy here [paragraph-false]wrapped in paragraphs\n\nwrapped in paragraphs[/paragraph-false] copy here",
            "<p>copy here </p><div>wrapped in paragraphs\n\nwrapped in paragraphs</div><p> copy here</p>",
        )

    def test_inherit(self):
        self._run_tests(
            ParagraphParser,
            "copy here [paragraph-inherit]wrapped in paragraphs\n\nwrapped in paragraphs[/paragraph-inherit] copy here",
            "<p>copy here </p><div><p>wrapped in paragraphs</p><p>wrapped in paragraphs</p></div><p> copy here</p>",
        )

    def test_inherit_deeper(self):
        self._run_tests(
            ParagraphParser,
            "copy here [paragraph-inherit]wrapped in paragraphs\n\nwrapped in paragraphs[paragraph-false][paragraph-inherit]no paragraphs here[/paragraph-inherit][/paragraph-false][/paragraph-inherit] copy here",
            "<p>copy here </p><div><p>wrapped in paragraphs</p><p>wrapped in paragraphs</p><div><div>no paragraphs here</div></div></div><p> copy here</p>",
        )

    def test_keep_newlines(self):
        self._run_tests(
            ParagraphParser,
            "p1\n\np2\np2 still\n\np3",
            "<p>p1</p><p>p2\np2 still</p><p>p3</p>",
        )


class StripNewlinesTest(BaseTest):
    def test_none(self):
        self._run_tests(
            StripNewlinesParser, "no newlines here", "no newlines here",
        )

    def test_all(self):
        self._run_tests(
            StripNewlinesParser,
            "remove\n all these\n\n new \n\n\n\nlines",
            "remove all these new lines",
        )

    def test_true(self):
        self._run_tests(
            StripNewlinesParser,
            "strip newlines here\n[stripnewlines-true]and also\n\n here[/stripnewlines-true]",
            "strip newlines here<div>and also here</div>",
        )

    def test_false(self):
        self._run_tests(
            StripNewlinesParser,
            "strip newlines here\n[stripnewlines-false]and also\n\n here[/stripnewlines-false]",
            "strip newlines here<div>and also here</div>",
        )

    def test_inherit(self):
        self._run_tests(
            StripNewlinesParser,
            "strip newlines here\n[stripnewlines-inherit]and also\n\n here[/stripnewlines-inherit]",
            "strip newlines here<div>and also here</div>",
        )

    def test_inherit_deep(self):
        self._run_tests(
            StripNewlinesParser,
            "strip newlines here\n[stripnewlines-inherit]and also\n\n here[stripnewlines-false][stripnewlines-inherit]these wont\n\n\n\n go[/stripnewlines-inherit][/stripnewlines-false][/stripnewlines-inherit]",
            "strip newlines here<div>and also here<div><div>these wont go</div></div></div>",
        )


class NewlinesParagraphsTest(BaseTest):
    def test_words(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "first paragraph\n\nsecond paragraph with newline\nand more content",
            "<p>first paragraph</p><p>second paragraph with newline<br />and more content</p>",
        )

    def test_inline(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "first paragraph\n\nsecond [b]paragraph[/b] with [i]newline\nand more[/i] content",
            "<p>first paragraph</p><p>second <strong>paragraph</strong> with <em>newline<br />and more</em> content</p>",
        )

    def test_block(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "[div]block to start[/div]then some copy[div]and another block\n\nand paragraph[/div]\n\nwith another paragraph",
            "<div><p>block to start</p></div><p>then some copy</p><div><p>and another block</p><p>and paragraph</p></div><p>with another paragraph</p>",
        )

    def test_inline_block(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "[b]bold text[/b]\nline break[div][i]italic content[/i][/div]",
            "<p><strong>bold text</strong><br />line break</p><div><p><em>italic content</em></p></div>",
        )

    def test_no_br_in_between_blocks(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "[div]This is a block[/div]\nThis content doesn't matter at all!",
            "<div><p>This is a block</p></div>\n<p>This content doesn&#x27;t matter at all!</p>",
        )

    def test_br_in_paragraph(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "[b]A really nice sentence[/b]\n[div]a div tag[/div]",
            "<p><strong>A really nice sentence</strong>\n</p><div><p>a div tag</p></div>",
        )

    def test_newlines_before_paragraph(self):
        self._run_tests(
            ParagraphNewlinesParser,
            "\n[b]A really nice sentence[/b]\n",
            "\n<p><strong>A really nice sentence</strong>\n</p>",
        )


class ParagraphsStripNewlinesTest(BaseTest):
    def test_words(self):
        self._run_tests(
            StripNewlinesNotParagraphsParser,
            "first paragraph\n\nsecond paragraph with newline\n and more content",
            "<p>first paragraph</p><p>second paragraph with newline and more content</p>",
        )

    def test_inline(self):
        self._run_tests(
            StripNewlinesNotParagraphsParser,
            "first paragraph\n\nsecond [b]paragraph[/b] with [i]newline\n and more[/i] content",
            "<p>first paragraph</p><p>second <strong>paragraph</strong> with <em>newline and more</em> content</p>",
        )

    def test_block(self):
        self._run_tests(
            StripNewlinesNotParagraphsParser,
            "[div]block to\n start[/div]then some\n copy[div]and another block\n\nand paragraph[/div]\n\nwith another paragraph",
            "<div><p>block to start</p></div><p>then some copy</p><div><p>and another block</p><p>and paragraph</p></div><p>with another paragraph</p>",
        )

    def test_inline_block(self):
        self._run_tests(
            StripNewlinesNotParagraphsParser,
            "[b]bold text[/b]\nline break[div][i]italic content[/i][/div]",
            "<p><strong>bold text</strong>line break</p><div><p><em>italic content</em></p></div>",
        )


class RenderSelectedTagsTest(BaseTest):
    def test_render_tags(self):
        self._run_tests(
            RenderSelectedTagsParser, "[b]bold text[/b]", "<strong>bold text</strong>",
        )

    def test_render_raw_missing_tags(self):
        self._run_tests(
            RenderSelectedTagsParser,
            "[b]bold text[/b][unknown]dunno about this[/unknown]",
            "<strong>bold text</strong>[unknown]dunno about this[/unknown]",
        )


class ParentScopeTest(BaseTest):
    def test_no_paragraphs(self):
        input_text = "Line 1\n\nLine 2\n\nLine 3"
        parser = DefaultParser(input_text)
        root_node = parser.root_node

        for node in root_node.tree:
            self.assertEqual(node._parent_node, root_node)

    def test_with_paragraphs(self):
        input_text = "Line 1\n\nLine 2\n\nLine 3"
        parser = ParagraphParser(input_text)
        root_node = parser.root_node

        for node in root_node.tree:
            self.assertEqual(node._parent_node, root_node)
