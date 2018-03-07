# -*- coding: utf-8 -*-
import unittest

from bbcondeparser import tags


class TestTagCategory(unittest.TestCase):
    def test_add_to_category(self):
        category = tags.TagCategory("Test Banana")

        class Tag1(tags.BaseTag):
            tag_name = 'peel'

        category.add_tag_cls(Tag1)

        expected_tag_classes = {Tag1}

        self.assertEqual(expected_tag_classes, category.tag_classes)

    def test_duplicate_tag(self):
        category = tags.TagCategory("Test apple")

        class Tag1(tags.BaseTag):
            tag_name = 'core'

        category.add_tag_cls(Tag1)

        with self.assertRaises(ValueError):
            category.add_tag_cls(Tag1)

    def test_as_decorator(self):
        category = tags.TagCategory("Test snake")

        class Grass(tags.BaseTag):
            tag_name = 'home'

        WrappedGrass = category(Grass)

        expected_tag_classes = {Grass}

        self.assertEqual(expected_tag_classes, category.tag_classes)
        self.assertIs(WrappedGrass, Grass)

    def test_remove_tag(self):
        category = tags.TagCategory('Test cow')

        class Tag1(tags.BaseTag):
            tag_name = 'milk'

        category.add_tag_cls(Tag1)
        category.remove_tag_cls(Tag1)

        expected_tag_classes = set()

        self.assertEqual(expected_tag_classes, category.tag_classes)


class TestAllowedTags(unittest.TestCase):
    def test_none_defined(self):
        class Tag(tags.BaseTag):
            tag_name = 'banana'

        expected_tags = None
        actual_tags = Tag.get_allowed_tags()

        self.assertEqual(expected_tags, actual_tags)

    def test_literal_tags(self):
        class SubTag1(tags.BaseTag):
            tag_name = 'peel'

        class SubTag2(tags.BaseTag):
            tag_name = 'segment'

        class OrangeTag(tags.BaseTag):
            tag_name = 'orange'
            allowed_tags = [SubTag1, SubTag2]

        expected_tags = {SubTag1, SubTag2}
        actual_tags = OrangeTag.get_allowed_tags()

        self.assertEqual(expected_tags, actual_tags)

    def test_literal_tags_duplicate(self):
        class SubTag1(tags.BaseTag):
            tag_name = 'peel'

        class SubTag2(tags.BaseTag):
            tag_name = 'segment'

        class OrangeTag(tags.BaseTag):
            tag_name = 'orange'
            allowed_tags = [SubTag1, SubTag2, SubTag1]

        expected_tags = {SubTag1, SubTag2}
        actual_tags = OrangeTag.get_allowed_tags()

        self.assertEqual(expected_tags, actual_tags)

    def test_tag_category(self):
        teletubbies = tags.TagCategory("Over the hills and far away")
        red_things = tags.TagCategory("Red things")

        class TellyTubby1(tags.BaseTag):
            tag_name = 'tinkywinky'
            tag_categories = [red_things, teletubbies]

        class TellyTubby2(tags.BaseTag):
            tag_name = 'dipsy'
            tag_categories = [teletubbies]

        class AngryChef(tags.BaseTag):
            tag_name = 'gordon'
            tag_categories = [red_things]

        class LikesRedThings(tags.BaseTag):
            tag_name = 'bull'
            allowed_tags = [red_things]

        class LikesTeletubbies(tags.BaseTag):
            tag_name = 'sun-baby'
            allowed_tags = [teletubbies]

        class LikesRedThingsAndTeletubbies(tags.BaseTag):
            tag_name = 'there-is-no-puncholine'
            allowed_tags = [teletubbies, red_things]

        self.assertEqual({TellyTubby1, AngryChef}, LikesRedThings.get_allowed_tags())
        self.assertEqual({TellyTubby1, TellyTubby2}, LikesTeletubbies.get_allowed_tags())
        self.assertEqual(
            {TellyTubby1, TellyTubby2, AngryChef},
            LikesRedThingsAndTeletubbies.get_allowed_tags(),
        )


class TestNewlineTextCount(unittest.TestCase):
    def test_add_newline(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.count, 2)


class TestNewlineTextRender(unittest.TestCase):
    def test_render_one_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(), tags.NEWLINE_STR)

    def test_render_two_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(), tags.NEWLINE_STR*2)

    def test_render_x_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(), tags.NEWLINE_STR*2)


class TestRawTextWordCount(unittest.TestCase):
    def test_rawtext_wordcount(self):
        inst = tags.RawText(u"this should become 5 words")
        self.assertEqual(inst.wordcount, 5)

    def test_some_punctuation(self):
        inst = tags.RawText(u"didn't you know hyponated-words count as one?")
        self.assertEqual(inst.wordcount, 7)

    def test_more_punctuation(self):
        inst = tags.RawText(
            u"""I'm going to put some "quotation" 'marks' and into this !"""
            """and some , spaces  between  some things ; punction . !! !"""
        )
        self.assertEqual(inst.wordcount, 17)

    def test_tabs(self):
        inst = tags.RawText(u'this\tuses\ttabs\t')
        self.assertEqual(inst.wordcount, 3)

    def test_missing_spaces_more(self):
        inst = tags.RawText(u"this.is.missing.spaces")
        self.assertEqual(inst.wordcount, 4)

    def test_unicode(self):
        inst = tags.RawText(u"æÞß 🍔 burgers for £100.")
        # emoji don't count as words
        self.assertEqual(inst.wordcount, 4)


class TestBaseNodeWordCount(unittest.TestCase):
    def test_no_children(self):
        class MyTag(tags.BaseTag):
            tag_name = 'a'
            pass
        inst = MyTag((), [], '[a]', '[/a]')
        self.assertEqual(inst.wordcount, 0)

    def test_some_children(self):
        # MC = MockWordCountChild
        class MC(object):
            def __init__(self, n):
                self.wordcount = n

        class MyTag(tags.BaseTag):
            tag_name = 'a'
            pass

        inst = MyTag((), [MC(5), MC(10), MC(0)], '[a]', '[/a]')
        self.assertEqual(inst.wordcount, 15)


class TestSimpleTagWordCount(unittest.TestCase):
    def test_no_children(self):
        class MySimpleTag(tags.SimpleTag):
            tag_name = 'a'
            template = 'all of the {} butts'.format(tags.SimpleTag.replace_text)

        inst = MySimpleTag((), [], '[a]', '[/a]')
        self.assertEqual(inst.wordcount, 4)

    def test_with_some_children(self):
        # MC = MockWordCountChild
        class MC(object):
            def __init__(self, n):
                self.wordcount = n

        class MySimpleTag(tags.SimpleTag):
            tag_name = 'a'
            template = 'this is my content : {}, did you like it?'.format(
                    tags.SimpleTag.replace_text)

        inst = MySimpleTag((), [MC(4), MC(0), MC(10)], '[a]', '[/a]')
        self.assertEqual(inst.wordcount, 22)

