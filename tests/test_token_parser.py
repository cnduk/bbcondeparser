from __future__ import print_function

import unittest

from bbcondeparser import token_parser

class TestSalvageTagOffset(unittest.TestCase):
    def test_open_no_attrs(self):
        input_str = '[bLorem Ipsum dolor'
        expected_offset = 7

        actual_offset = token_parser.salvage_tag_offset(input_str)

        self.assertEqual(expected_offset, actual_offset)

    def test_open_with_attrs_and_space(self):
        input_str = '[img src="www.bananas.com/banana.png" Lorem Ipsum dolor'
        expected_offset = 37

        actual_offset = token_parser.salvage_tag_offset(input_str)

        self.assertEqual(expected_offset, actual_offset)

    def test_open_with_attrs_no_space(self):
        input_str = '[img src="www.bananas.com/banana.png"Lorem Ipsum dolor'
        expected_offset = 37

        actual_offset = token_parser.salvage_tag_offset(input_str)

        self.assertEqual(expected_offset, actual_offset)

    def test_close(self):
        input_str = '[/b Lorem Ipsum is handy'
        expected_offset = 3

        actual_offset = token_parser.salvage_tag_offset(input_str)

        self.assertEqual(expected_offset, actual_offset)

    def test_only_open_char(self):
        input_str = '['
        expected_offset = 1

        actual_offset = token_parser.salvage_tag_offset(input_str)

        self.assertEqual(expected_offset, actual_offset)


class TestFindNextMultiChar(unittest.TestCase):
    def test_case_1(self):
        input_str = '01234567'
        chars = '56z'

        expected = 5

        result = token_parser.find_next_multi_char(input_str, chars)

        self.assertEqual(expected, result)

    def test_case_2(self):
        input_str = '0123a5a7b9'
        chars = 'ba'
        start = 7

        expected = 8

        result = token_parser.find_next_multi_char(input_str, chars, start)

        self.assertEqual(expected, result)

    def test_not_found(self):
        input_str = '0000000000'
        chars = 'pvfjaegsegr'

        expected = -1

        result = token_parser.find_next_multi_char(input_str, chars)

        self.assertEqual(expected, result)


class TestParseTag(unittest.TestCase):
    def test_alphanumeric_tag(self):
        input_str = '[h1]'
        expected = 'open_tag', 'h1', ()

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)


    def test_close_tag(self):
        input_str = '[/banana]'
        expected = 'close_tag', 'banana', None

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_bad_close_tag(self):
        input_str = "[/This isn't a close tag!]"
        expected = None

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_open_no_attrs(self):
        input_str = '[an-open-tag]'
        expected = 'open_tag', 'an-open-tag', ()

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_open_with_attrs(self):
        input_str = '[an-open-tag attr-a="Banana"  \t attr-b="apple" attr-b="this is a \\" double quote"]'
        expected_attrs = (
            ('attr-a', 'Banana'),
            ('attr-b', 'apple'),
            ('attr-b', r'this is a " double quote'),
        )
        expected = 'open_tag', 'an-open-tag', expected_attrs

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_bad_open_tag_name(self):
        input_str = '[a borked open tag]'
        expected = None

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_bad_open_tag_attrs(self):
        input_str = '[an-open-tag this="good" this="is" not=\'good\']'
        expected = None

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_open_tag_name_has_some_spaces(self):
        input_str = '[a      ]'
        expected = 'open_tag', 'a', ()

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)

    def test_close_tag_name_has_some_spaces(self):
        input_str = '[/a      ]'
        expected = 'close_tag', 'a', None

        result = token_parser.parse_tag(input_str)

        self.assertEqual(expected, result)


class TestBaseToken(unittest.TestCase):
    def test_repr(self):
        # This is just to make sure it doesn't do anything silly,
        # Not too concerned with the exact form.
        token = token_parser.BaseToken('something', (1, 2))
        repr(token)


class TestOpenTagTokenCreation(unittest.TestCase):
    _cls = token_parser.OpenTagToken

    def test_simple_open_tag(self):
        expected = self._cls('[bold]', (0, 6), 'bold', ())
        result = self._cls.generate_token(0, 'bold', ())
        self.assertEqual(expected, result)

    def test_simple_attr(self):
        expected = self._cls(
            '[colorize color="#ffaa00"]', (4, 30),
            'colorize', (('color', '#ffaa00'),),
        )
        result = self._cls.generate_token(
            4, 'colorize', {'color': '#ffaa00'},
        )
        self.assertEqual(expected, result)

    def test_dict_attrs_sorted(self):
        expected = self._cls(
            '[something a="a" b="b" c="c"]', (0, 29),
            'something', (('a', 'a'), ('b', 'b'), ('c', 'c')),
        )
        result = self._cls.generate_token(
            0, 'something', {'a':'a', 'b':'b', 'c':'c'},
        )
        self.assertEqual(expected, result)

    def test_multi_attr(self):
        expected = self._cls(
            '[choices a="first" b="second"]', (10, 40),
            'choices', (('a', 'first'), ('b', 'second')),
        )
        result = self._cls.generate_token(
            10, 'choices', (('a', 'first'), ('b', 'second')),
        )
        self.assertEqual(expected, result)

    def test_is_escaped(self):
        expected = self._cls(
            r'[thing a="hello\"world!\\"]', (0, 27),
            'thing', (('a', 'hello"world!\\'),),
        )
        result = self._cls.generate_token(
            0, 'thing', {'a': 'hello"world!\\'},
        )
        self.assertEqual(expected, result)


class TestTokenParser(unittest.TestCase):
    maxDiff = None

    def _testy(self, input_str, expected_tokens):
        actual_tokens = token_parser.get_tokens(input_str)

        try:
            self.assertEqual(expected_tokens, actual_tokens)
        except AssertionError:
            print("expected:", expected_tokens)
            print("actual:  ", actual_tokens)
            raise

    def test_empty(self):
        self._testy('', [])

    def test_just_text(self):
        input_str = "Lorem Ipsum dolor sit amet"
        expected_tokens = [
            token_parser.TextToken("Lorem Ipsum dolor sit amet", (0, 26)),
       ]
        self._testy(input_str, expected_tokens)

    def test_open_tag_no_attrs(self):
        input_str = "[a]"
        expected_tokens = [
            token_parser.OpenTagToken("[a]", (0, 3), 'a', ())
        ]
        self._testy(input_str, expected_tokens)

    def test_open_tag_no_attrs_some_space(self):
        input_str = "[a ]"
        expected_tokens = [
            token_parser.OpenTagToken("[a ]", (0, 4), 'a', ())
        ]
        self._testy(input_str, expected_tokens)

    def test_open_tag_with_attrs(self):
        input_str = r'[a x="x" y="bananas\"are\"awesome" x="a"]'
        expected_tokens = [
            token_parser.OpenTagToken(
                r'[a x="x" y="bananas\"are\"awesome" x="a"]',
                (0, 41),
                'a',
                (('x', 'x'), ('y', 'bananas"are"awesome'), ('x', 'a')),
            ),
        ]
        self._testy(input_str, expected_tokens)

    def test_open_tag_with_attrs_extra_space(self):
        input_str = r'[batamarang a="f" a="wow\""      ]'
        expected_tokens = [
            token_parser.OpenTagToken(
                r'[batamarang a="f" a="wow\""      ]',
                (0, 34),
                'batamarang',
                (('a', 'f'),('a', 'wow"')),
            ),
        ]
        self._testy(input_str, expected_tokens)

    def test_end_tag(self):
        input_str = '[/a]'
        expected_tokens = [
            token_parser.CloseTagToken('[/a]', (0, 4), 'a')
        ]
        self._testy(input_str, expected_tokens)

    def test_end_tag_with_some_space(self):
        input_str = '[/a    ]'
        expected_tokens = [
            token_parser.CloseTagToken('[/a    ]', (0, 8), 'a')
        ]
        self._testy(input_str, expected_tokens)

    def test_newline(self):
        input_str = '\n'
        expected_tokens = [token_parser.NewlineToken('\n', (0, 1))]
        self._testy(input_str, expected_tokens)

    def test_invalid_open_tag(self):
        input_str = '[bananas are the best!]'
        expected_tokens = [
            token_parser.BadSyntaxToken(
                '[bananas are the best!]', (0, 23), None
            ),
        ]
        self._testy(input_str, expected_tokens)

    def test_invalid_close_tag(self):
        input_str = '[/banana tree]'
        expected_tokens = [
            token_parser.BadSyntaxToken('[/banana tree]', (0, 14), None),
        ]
        self._testy(input_str, expected_tokens)

    def test_salvagable_invalid_open_tag_short_circuit(self):
        input_str = '[bananas [apples]'
        expected_tokens = [
            token_parser.BadSyntaxToken('[bananas', (0, 8), None),
            token_parser.TextToken(' ', (8, 9)),
            token_parser.OpenTagToken('[apples]', (9, 17), 'apples', ()),
        ]
        self._testy(input_str, expected_tokens)

    def test_salvagable_invalid_open_tag_eof(self):
        input_str = '[ba'
        expected_tokens = [
            token_parser.BadSyntaxToken('[ba', (0, 3), None),
        ]
        self._testy(input_str, expected_tokens)

    def test_salvagable_invalid_open_tag_with_attrs_end_of_file(self):
        input_str = r'[bananas skin="yellow" peel="\"yucky\"" my favourite is the banana!'
        expected_tokens = [
            token_parser.BadSyntaxToken(
                r'[bananas skin="yellow" peel="\"yucky\""',
                (0, 39), None
            ),
            token_parser.TextToken(" my favourite is the banana!", (39, 67)),
        ]

        self._testy(input_str, expected_tokens)

    def test_salvagable_invalid_tag_open_with_attrs_short_circuit(self):
        input_str = r'[bananas skin="yellow" peel="\"yucky\"" [b]my favourite is the banana![/b]'
        expected_tokens = [
            token_parser.BadSyntaxToken(
                r'[bananas skin="yellow" peel="\"yucky\""',
                (0, 39), None
            ),
            token_parser.TextToken(" ", (39, 40)),
            token_parser.OpenTagToken("[b]", (40, 43), 'b', ()),
            token_parser.TextToken("my favourite is the banana!", (43, 70)),
            token_parser.CloseTagToken("[/b]", (70, 74), 'b'),
        ]

        self._testy(input_str, expected_tokens)

    def test_salvagable_invalid_tag_open_end_of_file_with_newline(self):
        input_str = '[bananas Lorem Ipsum \n'
        expected_tokens = [
            token_parser.BadSyntaxToken('[bananas', (0, 8), None),
            token_parser.TextToken(' Lorem Ipsum ', (8, 21)),
            token_parser.NewlineToken('\n', (21, 22)),
        ]
        self._testy(input_str, expected_tokens)

    def test_empty_tag(self):
        input_str = '[]'
        expected_tokens = [token_parser.BadSyntaxToken('[]', (0, 2), None)]
        self._testy(input_str, expected_tokens)

    def test_newline_unix(self):
        input_str = u'\n'
        expected_tokens = [token_parser.NewlineToken(u'\n', (0, 1))]
        self._testy(input_str, expected_tokens)

    def test_newline_dos(self):
        input_str = u'\r\n'
        expected_tokens = [token_parser.NewlineToken(u'\r\n', (0, 2))]
        self._testy(input_str, expected_tokens)

    def test_mixed_newlines(self):
        # dos (\r\n), unix (\n), mac (\r),
        input_str = '\r\n\n\r'
        expected_tokens = [
            token_parser.NewlineToken('\r\n', (0, 2)),
            token_parser.NewlineToken('\n', (2, 3)),
            token_parser.NewlineToken('\r', (3, 4)),
        ]
        self._testy(input_str, expected_tokens)