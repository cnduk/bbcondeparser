import unittest

from bbcondeparser.tags import (
    RawText, ErrorText, BaseTag, BaseText, NewlineText, TagCategory,
    RootTag,
)
from bbcondeparser import tree_parser


class MockBaseTag(BaseTag):

    def __repr__(self):
        return self.pretty_format()


class TestCreateTagDict(unittest.TestCase):
    def test_ok(self):
        class Tag1(MockBaseTag):
            tag_name = 'apples'

        class Tag2(MockBaseTag):
            tag_name = 'bananas'

        class Tag3(MockBaseTag):
            tag_name = 'oranges'

        input_text = [Tag1, Tag2, Tag3, Tag2] # Duplicates are accepted
        expected = {'apples': Tag1, 'bananas': Tag2, 'oranges': Tag3}

        result = tree_parser.create_tag_dict(input_text)

        self.assertEqual(expected, result)

    def test_duplicate_name(self):
        class Tag1(MockBaseTag):
            tag_name = 'apples'

        class Tag2(MockBaseTag):
            tag_name = 'bananas'

        class Tag3(MockBaseTag):
            tag_name = 'apples'

        input_text = [Tag1, Tag2, Tag3]

        with self.assertRaises(ValueError):
            tree_parser.create_tag_dict(input_text)


class TestParseTree(unittest.TestCase):
    maxDiff = None

    def test_only_text(self):
        input_text = "Hello, World!"
        tags = []

        expected_tree = RootTag({}, [
            RawText("Hello, World!"),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_self_closing_tag(self):
        class Tag1(MockBaseTag):
            self_closing = True
            tag_name = 'apples'
            attr_defs = {'a': {}, 'b': {}}

        tags = [Tag1]
        input_text = r'[apples a="1" b="2" a="\" "]'

        expected_tree = RootTag({}, [
            ErrorText(r'[apples a="1" b="2" a="\" "]'),
#            Tag1(
#                (('a', '1'), ('b', '2'), ('a', '" ')),
#                [],
#                r'[apples a="1" b="2" a="\" "]',
#                '',
#            ),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_newline_closes_tag(self):
        class Tag1(MockBaseTag):
            close_on_newline = True
            tag_name = 'banana'

        tags = [Tag1]
        input_text = '[banana]A tag like this should turn the text yellow!\n'

        expected_tree = RootTag({}, [
            Tag1(
                (),
                [RawText('A tag like this should turn the text yellow!')],
                '[banana]',
                '',
            ),
            NewlineText('\n'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_multi_newline_closed_tag(self):
        class Tag1(MockBaseTag):
            close_on_newline = True
            tag_name = 'orange'

        tags = [Tag1]
        input_text = '[orange]This tag should make the text tangy!\n\n'

        expected_tree = RootTag({}, [
            Tag1(
                (),
                [RawText('This tag should make the text tangy!')],
                '[orange]',
                '',
            ),
            NewlineText('\n\n'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_not_closed(self):
        class Tag1(MockBaseTag):
            tag_name = 'mandarin'

        tags = [Tag1]
        input_text = 'Hello! [mandarin]This is some lovely text!'

        expected_tree = RootTag({}, [
            RawText('Hello! '),
            ErrorText('[mandarin]'),
            RawText('This is some lovely text!'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_invalid_close_tag(self):
        class Tag1(MockBaseTag):
            tag_name = 'cheese'

        class Tag2(MockBaseTag):
            tag_name = 'banana'

        tags = [Tag1, Tag2]
        input_text = '[cheese][/banana][/notexist][/cheese]'

        expected_tree = RootTag({}, [
            Tag1(
                (),
                [
                    ErrorText('[/banana]'),
                    ErrorText('[/notexist]'),
                ],
                '[cheese]',
                '[/cheese]',
            )
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_custom_tag_set(self):
        class InnerTag(MockBaseTag):
            tag_name = 'inner'

        class OuterTag(MockBaseTag):
            tag_name = 'banana'
            allowed_tags = [InnerTag]

        tags = [OuterTag]
        input_text = '[banana][inner]Hello![/inner][/banana]'

        expected_tree = RootTag({}, [
            OuterTag(
                (),
                [
                    InnerTag(
                        (),
                        [RawText('Hello!')],
                        '[inner]',
                        '[/inner]',
                    )
                ],
                '[banana]',
                '[/banana]',
            )
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_no_close_brace(self):
        input_text = '[imgoingtobreak'
        tags = []

        expected_tree = RootTag({}, [
            ErrorText('[imgoingtobreak'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_bad_tag_syntax(self):
        input_text = '[this is really broken!]'
        tags = []

        expected_tree = RootTag({}, [
            ErrorText('[this is really broken!]')
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_close_not_opened_tag(self):
        class Tag1(MockBaseTag):
            tag_name = 'apple'

        input_text = '[/apple]'
        tags = [Tag1]

        expected_tree = RootTag({}, [
            ErrorText('[/apple]')
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_empty_tag(self):
        input_text = '[]'
        tags = []

        expected_tree = RootTag({}, [
            ErrorText('[]')
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_close_outer_tag(self):
        class Tag1(MockBaseTag):
            tag_name = 'a'

        class Tag2(MockBaseTag):
            tag_name = 'b'

        input_text = '[a][b][/a][/b]'
        tags = [Tag1, Tag2]

        expected_tree = RootTag({}, [
            Tag1((), [ErrorText('[b]')], '[a]', '[/a]'),
            ErrorText('[/b]'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_close_outer_tag_newline(self):
        class Tag1(MockBaseTag):
            tag_name = 'a'
            close_on_newline = True

        class Tag2(MockBaseTag):
            tag_name = 'b'

        input_text = '[a][b]\n[/b]'
        tags = [Tag1, Tag2]

        expected_tree = RootTag({}, [
            Tag1((), [ErrorText('[b]')], '[a]', ''),
            NewlineText('\n'),
            ErrorText('[/b]'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_close_outer_tag_newline_multi(self):
        class Tag1(MockBaseTag):
            tag_name = 'a'
            close_on_newline = True

        input_text = '[a][a][a]text\n[/a][/a]'
        tags = [Tag1]

        expected_tree = RootTag({}, [
            Tag1((), [
                Tag1((), [
                    Tag1((), [RawText("text")], '[a]', ''),
                ], '[a]', ''),
            ], '[a]', ''),
            NewlineText('\n'),
            ErrorText("[/a]"),
            ErrorText("[/a]"),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)
        self.assertEqual(expected_tree, result)

    def test_custom_tag_set_complex(self):
        class InnerTag1(MockBaseTag):
            tag_name = 'inner-a'

        class InnerTag2(MockBaseTag):
            tag_name = 'inner-b'
            self_closing = True

        class OuterTag1(MockBaseTag):
            tag_name = 'outer-banana'
            allowed_tags = [InnerTag1, InnerTag2]

        class OuterTag2(MockBaseTag):
            tag_name = 'outer-apple'
            allowed_tags = [InnerTag1]

        tags = [OuterTag1, OuterTag2]
        # Text written like this so that don't have to deal with loads of newlines
        input_text = (
            '[outer-banana]'
                '[inner-a]Hello[/inner-a]'
                '[inner-b]'
                '[outer-banana]fail[/outer-banana]'
                '[outer-apple]also fail[/outer-apple]'
            '[/outer-banana]'
            '[outer-apple]'
                '[inner-a]This works![/inner-a]'
                '[inner-b]'
                '[outer-banana]also also also fail[/outer-banana]'
                '[outer-apple]applefail[/outer-apple]'
            '[/outer-apple]'
            '[inner-a]Should be inside something![/inner-a]'
            '[inner-b]'
        )

        expected_tree = RootTag({}, [
             OuterTag1((),
                 [
                     InnerTag1((),[RawText("Hello")],'[inner-a]','[/inner-a]'),
                     InnerTag2((),[],'[inner-b]',''),
                     OuterTag1.null_class((), [RawText('fail')], '[outer-banana]', '[/outer-banana]'),
                     OuterTag2.null_class((), [RawText('also fail')], '[outer-apple]', '[/outer-apple]'),
                 ],
                 '[outer-banana]','[/outer-banana]',
             ),
            OuterTag2((),
                 [
                     InnerTag1((),[RawText("This works!")],'[inner-a]','[/inner-a]'),
                     ErrorText('[inner-b]'),
                     OuterTag1.null_class((), [RawText('also also also fail')], '[outer-banana]', '[/outer-banana]'),
                     OuterTag2.null_class((), [RawText('applefail')], '[outer-apple]', '[/outer-apple]'),
                 ],
                 '[outer-apple]','[/outer-apple]',
             ),
             ErrorText('[inner-a]'), RawText('Should be inside something!'), ErrorText('[/inner-a]'),
             ErrorText('[inner-b]'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_ctx_honoured_in_error_short_circuit_closetag(self):
        class InnerTag(MockBaseTag):
            tag_name = 'C'
            self_closing = True
            allowed_tags = []

        class MiddleTag(MockBaseTag):
            tag_name = 'B'
            allowed_tags = [InnerTag]

        class OuterTag(MockBaseTag):
            tag_name = 'A'
            allowed_tags = [MiddleTag]

        tags = [OuterTag]
        input_text = '[A][B][C][/A]'

        # So in this example, we need to ensure that when we get to the
        # close A, we correctly assert that the open B is missing its close
        # tag, so it is in error. We then also need to ensure we re-evaluate
        # the C tag. As B is missing its close, we do not know its scope,
        # so we the C is hoisted up into A's scope, and it is not valid
        # under A's scope (and is not a registered "ignored" tag),
        # so it needs to be marked error as well.

        # This is obvious, but was missed in the first couple iteration of the
        # tree parser, and I wanted to ensure that this situation makes sense.

        expected_tree = RootTag({}, [
            OuterTag((),
                [
                    ErrorText("[B]"),
                    ErrorText("[C]"),
                ],
                '[A]', '[/A]',
            ),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_ctx_honoured_in_error_short_circuit_newline(self):
        # See above, also awfully named function for explanation
        # test_tag_ctx_honoured_in_error_short_circuit_closetag
        class InnerTag(MockBaseTag):
            tag_name = 'C'
            self_closing = True
            allowed_tags = []

        class MiddleTag(MockBaseTag):
            tag_name = 'B'
            allowed_tags = [InnerTag]

        class OuterTag(MockBaseTag):
            tag_name = 'A'
            allowed_tags = [MiddleTag]
            close_on_newline = True

        tags = [OuterTag]
        input_text = '[A][B][C]\n'

        expected_tree = RootTag({}, [
            OuterTag((),
                [
                    ErrorText("[B]"),
                    ErrorText("[C]"),
                ],
                '[A]', '',
            ),
            NewlineText('\n'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_ctx_honoured_in_error_EOF(self):
        # See above, also awfully named function for explanation
        # test_tag_ctx_honoured_in_error_short_circuit_closetag
        class InnerTag(MockBaseTag):
            tag_name = 'B'
            self_closing = True

        class OuterTag(MockBaseTag):
            tag_name = 'A'
            allowed_tags = [InnerTag]

        tags = [OuterTag]

        input_text = '[A][B]'

        expected_tree = RootTag({}, [
            ErrorText("[A]"),
            ErrorText("[B]"),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_generic_1(self):
        class Tag1(MockBaseTag):
            tag_name = 'a'
            self_closing = True

        class Tag2(MockBaseTag):
            tag_name = 'b'
            attr_defs = {'x': {}, 'y': {}}

        tags = [Tag1, Tag2]

        input_text = r'[a][b x="z" y="a \" banana"]Hello, world![/b]'

        expected_tree = RootTag({}, [
            Tag1((), [], '[a]', ''),
            Tag2(
                (('x', 'z'),('y', 'a " banana')),
                [RawText("Hello, world!")],
                r'[b x="z" y="a \" banana"]',
                '[/b]',
            )
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_generic_2(self):
        ACat = TagCategory('A')
        BCat = TagCategory('B')

        class ATag(MockBaseTag):
            tag_name = 'A'
            allowed_tags = [BCat]
            tag_categories = [ACat]

        class BTag(MockBaseTag):
            tag_name = 'B'
            allowed_tags = [ACat]
            tag_categories = [BCat]

        tags = [ATag]
        input_text = '[A][B][A][/A][/A]'

        expected_tree = RootTag({}, [
            ATag((), [
                ErrorText('[B]'), # missing close
                ATag.null_class((), [], '[A]', '[/A]'), # Not allowed in context of A
            ], '[A]', '[/A]'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

class TestTreeParser(unittest.TestCase):
    def test_parser(self):
        class Bold(MockBaseTag):
            tag_name = 'b'
            def _render(self):
                return '<b>{}</b>'.format(self.render_children())

        class Italic(MockBaseTag):
            tag_name = 'i'
            def _render(self):
                return '<i>{}</i>'.format(self.render_children())

        class ToBeIgnored(MockBaseTag):
            tag_name = 'ignored'
            def _render(self):
                return "I SHOULD HAVE BEEN IGNORED"

        class UpperCaseText(BaseText):
            def _render(self):
                return self.text.upper()

        input_text = "[b][i][ignored]It's not a tumor![/ignored][/i][/b]"

        expected_text = "<b><i>IT'S NOT A TUMOR!</i></b>"

        class TestParser(tree_parser.BaseTreeParser):
            tags = [Bold, Bold, Italic]
            ignored_tags = [ToBeIgnored]

            raw_text_class = UpperCaseText

        inst = TestParser(input_text)
        result_text = inst.render()

        self.assertEqual(expected_text, result_text)


class TestTreeParserNewline(unittest.TestCase):
    def test_newline_tag(self):
        input_text = 'butts\nbutts'
        expected_tree = RootTag({}, [
            RawText('butts'),
            NewlineText('\n'),
            RawText('butts'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, [])

        self.assertEqual(expected_tree, result)


    def test_newline_concat(self):
        input_text = 'butts\n\nbutts\n\n\nbutts'
        expected_tree = RootTag({}, [
            RawText('butts'),
            NewlineText('\n\n'),
            RawText('butts'),
            NewlineText('\n\n\n'),
            RawText('butts'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, [])

        self.assertEqual(expected_tree, result)

    def test_dosnewline(self):
        input_text = 'butts\r\nbutts'
        expected_tree = RootTag({}, [
            RawText('butts'),
            NewlineText('\r\n'),
            RawText('butts'),
        ], '', '')

        result = tree_parser.parse_tree(input_text, [])

        self.assertEqual(expected_tree, result)

class TestBadToken(unittest.TestCase):
    def test_error_raised_unknown_token_type(self):
        inst = tree_parser._TreeParser('', [])
        inst.tokens = [object()]
        with self.assertRaises(TypeError):
            inst.parse_tree()


class TestTreeParserContext(unittest.TestCase):

    def test_context_passed(self):
        class Bold(MockBaseTag):
            tag_name = 'b'

            def _render(self):
                ctx = self.get_context()
                return '<b>{bold}. {children}</b>'.format(
                    bold=ctx.get('b'),
                    children=self.render_children(),
                )

        class Italic(MockBaseTag):
            tag_name = 'i'

            def _render(self):
                ctx = self.get_context()
                return '<i>{italic}. {children}</i>'.format(
                    italic=ctx.get('i'),
                    children=self.render_children()
                )

        class TestParser(tree_parser.BaseTreeParser):
            tags = [Bold, Italic]

        input_text = "[b][i]It's not a tumor![/i][/b]"
        expected_text = "<b>bold. <i>italic. It's not a tumor!</i></b>"

        inst = TestParser(input_text)
        result_text = inst.render(ctx={
            'b': 'bold',
            'i': 'italic',
        })

        self.assertEqual(expected_text, result_text)

    def test_context_updates(self):
        class Bold(MockBaseTag):
            tag_name = 'b'

            def _render(self):
                return '<b>{bold}. {children}</b>'.format(
                    bold='italic',
                    children=self.render_children(),
                )

        class Italic(MockBaseTag):
            tag_name = 'i'

            def _render(self):
                ctx = self.get_context()
                return '<i>{italic}. {children}</i>'.format(
                    italic=ctx.get('i'),
                    children=self.render_children()
                )

        class TestParser(tree_parser.BaseTreeParser):
            tags = [Bold, Italic]

        input_text = "[b][i]It's not a tumor![/i][/b]"
        expected_text = "<b>italic. <i>italic. It's not a tumor!</i></b>"

        inst = TestParser(input_text)
        result_text = inst.render(ctx={
            'b': 'bold',
            'i': 'italic',
        })

        self.assertEqual(expected_text, result_text)

    def test_context_tag_updates(self):
        class Bold(MockBaseTag):
            tag_name = 'b'

            def _render(self):
                ctx = self.get_context()
                return '<b>{bold}. {children}</b>'.format(
                    bold=ctx.get('b', 'BOLD'),
                    children=self.render_children(),
                )

        class Italic(MockBaseTag):
            tag_name = 'i'

            def _render(self):
                ctx = self.get_context()
                return '<i>{italic}. {children}</i>'.format(
                    italic=ctx.get('i', 'ITALIC'),
                    children=self.render_children()
                )

        class TestParser(tree_parser.BaseTreeParser):
            tags = [Bold, Italic]

        input_text = "[b][i]It's not a tumor![/i][/b]"
        expected_text = "<b>NOT BOLD. <i>ITALIC. It's not a tumor!</i></b>"

        inst = TestParser(input_text)
        result_text = inst.render(ctx={
            'b': 'NOT BOLD',
        })

        self.assertEqual(expected_text, result_text)
