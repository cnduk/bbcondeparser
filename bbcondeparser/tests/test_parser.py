import unittest

from bbcondeparser.tags import RawText, ErrorText, BaseTag
from bbcondeparser import parser


class MockBaseTag(BaseTag):
    def __init__(self, *args, **kwargs):
        super(MockBaseTag, self).__init__(*args, **kwargs)
        self.__init_with = args, kwargs

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False

        return self.__init_with == other.__init_with

    def __repr__(self):
        return "MockBaseTag({}, {})".format(
            super(MockBaseTag, self).__repr__(),
            str(self.__init_with)
        )

class TestFindNextMultiChar(unittest.TestCase):
    def test_case_1(self):
        input = '01234567'
        chars = '56z'

        expected = 5

        result = parser.find_next_multi_char(input, chars)

        self.assertEqual(expected, result)

    def test_case_2(self):
        input = '0123a5a7b9'
        chars = 'ba'
        start = 7

        expected = 8

        result = parser.find_next_multi_char(input, chars, start)

        self.assertEqual(expected, result)

    def test_not_found(self):
        input = '0000000000'
        chars = 'pvfjaegsegr'

        expected = -1

        result = parser.find_next_multi_char(input, chars)

        self.assertEqual(expected, result)




class TestParseTag(unittest.TestCase):
    def test_close_tag(self):
        input = '/banana'
        expected = parser.TAG_END, 'banana', None

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_close_tag(self):
        input = "/This isn't a close tag!"
        expected = None

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_open_no_attrs(self):
        input = 'an-open-tag'
        expected = parser.TAG_START, 'an-open-tag', ()

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_open_with_attrs(self):
        input = 'an-open-tag attr-a="Banana"  \t attr-b="apple" attr-b="this is a \\" double quote"'
        expected_attrs = (
            ('attr-a', 'Banana'),
            ('attr-b', 'apple'),
            ('attr-b', r'this is a " double quote'),
        )
        expected = parser.TAG_START, 'an-open-tag', expected_attrs

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_open_tag_name(self):
        input = 'a borked open tag'
        expected = None

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)

    def test_bad_open_tag_attrs(self):
        input = 'an-open-tag this="good" this="is" not=\'good\''
        expected = None

        result = parser.parse_tag(input)

        self.assertEqual(expected, result)


class TestCreateTagDict(unittest.TestCase):
    def test_ok(self):
        class Tag1(object):
            tag_name = 'apples'

        class Tag2(object):
            tag_name = 'bananas'

        class Tag3(object):
            tag_name = 'oranges'

        input = [Tag1, Tag2, Tag3, Tag2] # Duplicates are accepted
        expected = {'apples': Tag1, 'bananas': Tag2, 'oranges': Tag3}

        result = parser.create_tag_dict(input)

        self.assertEqual(expected, result)

    def test_duplicate_name(self):
        class Tag1(object):
            tag_name = 'apples'

        class Tag2(object):
            tag_name = 'bananas'

        class Tag3(object):
            tag_name = 'apples'

        input = [Tag1, Tag2, Tag3]

        with self.assertRaises(RuntimeError):
            parser.create_tag_dict(input)


class TestParseTree(unittest.TestCase):
    def test_only_text(self):
        input_text = "Hello, World!"
        tags = []

        expected_tree = [RawText("Hello, World!")]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_self_closing_tag(self):
        class Tag1(MockBaseTag):
            self_closing = True
            tag_name = 'apples'

        tags = [Tag1]
        input_text = r'[apples a="1" b="2" a="\" "]'

        expected_tree = [
            Tag1(
                (('a', '1'), ('b', '2'), ('a', '" ')),
                [],
                r'[apples a="1" b="2" a="\" "]',
                '',
            ),
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_newline_closes_tag(self):
        class Tag1(MockBaseTag):
            close_on_newline = True
            tag_name = 'banana'

        tags = [Tag1]
        input_text = '[banana]A tag like this should turn the text yellow!\n'

        expected_tree = [
            Tag1(
                (),
                [RawText('A tag like this should turn the text yellow!')],
                '[banana]',
                '\n',
            )
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_tag_not_closed(self):
        class Tag1(MockBaseTag):
            tag_name = 'mandarin'

        tags = [Tag1]
        input_text = 'Hello! [mandarin]This is some lovely text!'

        expected_tree = [
            RawText('Hello! '),
            ErrorText('[mandarin]'),
            RawText('This is some lovely text!'),
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_invalid_close_tag(self):
        class Tag1(MockBaseTag):
            tag_name = 'cheese'

        class Tag2(MockBaseTag):
            tag_name = 'banana'

        tags = [Tag1, Tag2]
        input_text = '[cheese][/banana][/notexist][/cheese]'

        expected_tree = [
            Tag1(
                (),
                [
                    ErrorText('[/banana]'),
                    ErrorText('[/notexist]'),
                ],
                '[cheese]',
                '[/cheese]',
            )
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_customer_tag_set(self):
        class InnerTag(MockBaseTag):
            tag_name = 'inner'

        class OuterTag(MockBaseTag):
            tag_name = 'banana'
            tag_set = [InnerTag]

        tags = [OuterTag]
        input_text = '[banana][inner]Hello![/inner][/banana]'

        expected_tree = [
            OuterTag(
                (),
                [
                    InnerTag(
                        (),
                        [RawText('Hello!')],
                        '[inner1]',
                        '[/inner1]',
                    )
                ],
                '[banana]',
                '[/banana]',
            )
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)

    def test_custom_tag_set_complex(self):
        #TODO
        self.skipTest("notimplemented")
        class InnerTag1(MockBaseTag):
            tag_name = 'inner_1'

        class InnerTag2(MockBaseTag):
            tag_name = 'inner_2'
            self_closing = True

        class OuterTag1(MockBaseTag):
            tag_name = 'outer_banana'
            tag_set = [InnerTag1, InnerTag2]

        class OuterTag2(MockBaseTag):
            tag_name = 'outer_apple'
            tag_set = [InnerTag1]

        tags = [OuterTag1, OuterTag2]
        input_text = ''

    def test_generic_1(self):
        class Tag1(MockBaseTag):
            tag_name = 'a'
            self_closing = True

        class Tag2(MockBaseTag):
            tag_name = 'b'

        tags = [Tag1, Tag2]

        input_text = r'[a][b x="z" y="a \" banana"]Hello, world![/b]'

        expected_tree = [
            Tag1((), [], '[a]', ''),
            Tag2(
                (('x', 'z'),('y', 'a " banana')),
                [RawText("Hello, world!")],
                r'[b x="z" y="a \" banana"]',
                '[/b]',
            )
        ]

        result = parser.parse_tree(input_text, tags)

        self.assertEqual(expected_tree, result)