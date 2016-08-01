from __future__ import print_function

import unittest
import mock

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
        input = '01234567'
        chars = '56z'

        expected = 5

        result = token_parser.find_next_multi_char(input, chars)

        self.assertEqual(expected, result)

    def test_case_2(self):
        input = '0123a5a7b9'
        chars = 'ba'
        start = 7

        expected = 8

        result = token_parser.find_next_multi_char(input, chars, start)

        self.assertEqual(expected, result)

    def test_not_found(self):
        input = '0000000000'
        chars = 'pvfjaegsegr'

        expected = -1

        result = token_parser.find_next_multi_char(input, chars)

        self.assertEqual(expected, result)


class TestParseTag(unittest.TestCase):
    def test_close_tag(self):
        input = '[/banana]'
        expected = 'close_tag', 'banana', None

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_close_tag(self):
        input = "[/This isn't a close tag!]"
        expected = None

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_open_no_attrs(self):
        input = '[an-open-tag]'
        expected = 'start_tag', 'an-open-tag', ()

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_open_with_attrs(self):
        input = '[an-open-tag attr-a="Banana"  \t attr-b="apple" attr-b="this is a \\" double quote"]'
        expected_attrs = (
            ('attr-a', 'Banana'),
            ('attr-b', 'apple'),
            ('attr-b', r'this is a " double quote'),
        )
        expected = 'start_tag', 'an-open-tag', expected_attrs

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_open_tag_name(self):
        input = '[a borked open tag]'
        expected = None

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_open_tag_attrs(self):
        input = '[an-open-tag this="good" this="is" not=\'good\']'
        expected = None

        result = token_parser.parse_tag(input)

        self.assertEqual(expected, result)


class TestBaseToken(unittest.TestCase):
    def test_repr(self):
        # This is just to make sure it doesn't do anything silly,
        # Not too concerned with the exact form.
        token = token_parser.BaseToken('something', (1, 2))
        repr(token)


class TestTokenParser(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        # 'cause we also want to compare the attrs
        # (but in the normal running, we don't, which is why the
        # code doesn't include the attrs in the comparison)
        class mock_OpenTagToken(token_parser.OpenTagToken):
            def __init__(self, text, location, tag_name, attrs):
                # have to overwrite this, because otherwise the way we're
                # patching messes things up, brah.
                token_parser.BaseToken.__init__(self, text, location)
                self.tag_name = tag_name
                self.attrs = attrs

            def __eq__(self, other):
                return super(mock_OpenTagToken, self).__eq__(other) \
                    and self.attrs == other.attrs

        patch = mock.patch(
            'bbcondeparser.token_parser.OpenTagToken',
            new=mock_OpenTagToken
        )
        patch.start()
        self.addCleanup(patch.stop)

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






