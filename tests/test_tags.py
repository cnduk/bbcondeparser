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

        with self.assertRaises(RuntimeError):
            category.add_tag_cls(Tag1)

    def test_as_decorator(self):
        category = tags.TagCategory("Test snake")

        class Grass(tags.BaseTag):
            tag_name = 'home'

        WrappedGrass = category(Grass)

        expected_tag_classes = {Grass}

        self.assertEqual(expected_tag_classes, category.tag_classes)
        self.assertIs(WrappedGrass, Grass)


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


class TestBaseMetaTags(unittest.TestCase):
    def test_newlin_runtime_error(self):

        with self.assertRaises(RuntimeError):
            class BadTag(tags.BaseTag):
                tag_name = 'bad_tag'
                strip_newlines = True
                convert_newlines = True


class TestNewlineTextCount(unittest.TestCase):
    def test_add_newline(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.count, 2)


class TestNewlineTextRender(unittest.TestCase):
    def test_render_one_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(False), tags.NEWLINE_STR)

    def test_render_two_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(False), tags.NEWLINE_STR*2)

    def test_render_x_line(self):
        test_newline = tags.NewlineText(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        test_newline.add_newline(tags.NEWLINE_STR)
        self.assertEqual(test_newline.render(False), tags.NEWLINE_STR*2)
