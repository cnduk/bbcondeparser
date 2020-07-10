import unittest

from bbcondeparser.tags import (
    RawText,
    ErrorText,
    BaseTag,
    BaseText,
    NewlineText,
    TagCategory,
    RootTag,
    SimpleTag,
)
from bbcondeparser import tree_parser


class MockRootTag(RootTag):
    def __repr__(self):
        return self.pretty_format()


class MockBaseTag(BaseTag):
    def __repr__(self):
        return self.pretty_format()


class TestB(SimpleTag):
    tag_name = "b"
    template = "<b>{{ body }}</b>"


class MockTreeParser(tree_parser.BaseTreeParser):
    root_tag_class = MockRootTag


class TestAttributes(unittest.TestCase):
    def _test(self, input_text, expected_text, expected_tree, parser):
        inst = parser(input_text)
        result_text = inst.render()
        result_tree = inst.root_node

        self.assertEqual(expected_tree, result_tree)
        self.assertEqual(expected_text, result_text)

    def test_missing_attr_self_closing(self):
        class TestTag(MockBaseTag):
            tag_name = "r"
            self_closing = True
            attr_defs = {"required": {}}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = "[r]"
        expected_text = "[r]"
        expected_tree = MockRootTag({}, [ErrorText("[r]")], "", "")

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_extra_attr_self_closing(self):
        class TestTag(MockBaseTag):
            tag_name = "e"
            self_closing = True
            attr_defs = {}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = '[e required="no"]'
        expected_text = '[e required="no"]'
        expected_tree = MockRootTag({}, [ErrorText('[e required="no"]')], "", "")

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_not_allowed_duplicate_self_closing(self):
        class TestTag(MockBaseTag):
            tag_name = "d"
            self_closing = True
            attr_defs = {"just-one-please": {}}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = '[d just-one-please="first" just-one-please="second"]'
        expected_text = '[d just-one-please="first" just-one-please="second"]'
        expected_tree = MockRootTag(
            {},
            [ErrorText('[d just-one-please="first" just-one-please="second"]')],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_missing_attr(self):
        class TestTag(MockBaseTag):
            tag_name = "r"
            attr_defs = {"required": {}}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag, TestB]

        input_text = "[r][b]hello[/b]world[/r]"
        expected_text = "[r]<b>hello</b>world[/r]"
        expected_tree = MockRootTag(
            {},
            [
                ErrorText("[r]"),
                TestB({}, [RawText("hello"),], "[b]", "[/b]"),
                RawText("world"),
                ErrorText("[/r]"),
            ],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_extra_attr(self):
        class TestTag(MockBaseTag):
            tag_name = "e"
            attr_defs = {}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag, TestB]

        input_text = '[e required="no"][b]hello[/b]world[/e]'
        expected_text = '[e required="no"]<b>hello</b>world[/e]'
        expected_tree = MockRootTag(
            {},
            [
                ErrorText('[e required="no"]'),
                TestB({}, [RawText("hello"),], "[b]", "[/b]"),
                RawText("world"),
                ErrorText("[/e]"),
            ],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_not_allowed_duplicate(self):
        class TestTag(MockBaseTag):
            tag_name = "d"
            attr_defs = {"just-one-please": {}}

            def _render(self):
                return "I should not have rendered"

        class TestParser(MockTreeParser):
            tags = [TestTag, TestB]

        input_text = (
            '[d just-one-please="first" just-one-please="second"]'
            "[b]hello[/b]world[/d]"
        )
        expected_text = (
            '[d just-one-please="first" just-one-please="second"]'
            "<b>hello</b>world[/d]"
        )
        expected_tree = MockRootTag(
            {},
            [
                ErrorText('[d just-one-please="first" just-one-please="second"]'),
                TestB({}, [RawText("hello"),], "[b]", "[/b]"),
                RawText("world"),
                ErrorText("[/d]"),
            ],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_default_value(self):
        class TestTag(MockBaseTag):
            tag_name = "d"
            attr_defs = {"a": {"default": "1"}}

            def _render(self):
                return "<d>" + self.attrs["a"] + "</d>"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = "[d]cheesecake is yummy[/d]"
        expected_text = "<d>1</d>"
        expected_tree = MockRootTag(
            {},
            [TestTag([("d", "1")], [RawText("cheesecake is yummy")], "[b]", "[/b]"),],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_default_value_overriden(self):
        class TestTag(MockBaseTag):
            tag_name = "d"
            attr_defs = {"a": {"default": "1"}}

            def _render(self):
                return "<d>" + self.attrs["a"] + "</d>"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = '[d a="hello"]cheesecake is yummy[/d]'
        expected_text = "<d>hello</d>"
        expected_tree = MockRootTag(
            {},
            [
                TestTag(
                    [("a", "hello")], [RawText("cheesecake is yummy")], "[b]", "[/b]"
                ),
            ],
            "",
            "",
        )

        self._test(input_text, expected_text, expected_tree, TestParser)

    def test_default_value_none(self):
        class TestTag(MockBaseTag):
            tag_name = "d"
            attr_defs = {"a": {"default": None}}
            self_closing = True

            def _render(self):
                if self.attrs["a"] is None:
                    return "success"
                return "fail"

        class TestParser(MockTreeParser):
            tags = [TestTag]

        input_text = "[d]"
        expected_text = "success"
        expected_tree = MockRootTag({}, [TestTag([], [], "[b]", ""),], "", "")

        self._test(input_text, expected_text, expected_tree, TestParser)

