# Copyright (c) 2017 Conde Nast Britain
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

from . import _six as six


NEWLINE_STR = '\n'


class BaseNode(object):

    def __init__(self):
        self._parent_node = None

    def set_parent_node(self, parent_node):
        self._parent_node = parent_node

    def get_context(self):
        if self._parent_node:
            return self._parent_node.get_context()
        return {}

    def render(self):
        return self._render()

    def _render(self):
        raise NotImplementedError


class BaseText(BaseNode):
    def __init__(self, text):
        super(BaseText, self).__init__()
        self.text = text

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, repr(self.text))

    def _render(self):
        return self.text

    def render_raw(self):
        return self.text


class RawText(BaseText):
    """This class is to hold chunks of plain text.
        handles escaping html within the text.
    """
    pass


class NewlineText(BaseText):
    DOUBLE_NEWLINE = NEWLINE_STR * 2

    def __init__(self, *args, **kwargs):
        super(NewlineText, self).__init__(*args, **kwargs)
        self.count = 1

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    def add_newline(self, text):
        self.count += 1
        self.text += text

    def _render(self):
        return NEWLINE_STR if self.count == 1 else self.DOUBLE_NEWLINE


class ErrorText(BaseText):
    """This class is to hold source text which could not be parsed.
        handles escaping html within the text.
    """
    def __init__(self, text, reason=None):
        """`text` - the invalid text from the markup source
            `reason` - why the source text was considered invalid
        """
        super(ErrorText, self).__init__(text)
        self.reason = reason

    def __repr__(self):
        return "{}('{}': {})".format(
            self.__class__.__name__, self.reason, repr(self.text),
        )


class BaseTagMeta(type):
    def __new__(cls, name, bases, ctx):
        new_cls = super(BaseTagMeta, cls).__new__(cls, name, bases, ctx)

        cls.validate_tag_cls(new_cls)

        if new_cls.tag_name is not None:
            def render(self):
                return self.render_children()

            # We force this to be a string as python2 internals does not like
            # unicode class names.
            null_name = str('Null{}'.format(name))
            null_ctx = dict(ctx)
            null_ctx.pop('__classcell__', None)
            null_ctx['render'] = render
            new_null_cls = super(BaseTagMeta, cls).__new__(
                cls, null_name, bases, null_ctx)

            new_cls.null_class = new_null_cls
            new_null_cls.null_class = new_null_cls

            for category in new_cls.tag_categories:
                category.add_tag_cls(new_cls)

        return new_cls

    @staticmethod
    def validate_tag_cls(tag_cls):
        # TODO `close_on_newline` vs `self_closing`
        # TODO `self_closing` vs `allowed_tags`
        # tag_name warning malformed?
        # category shouldbe TagCategory instance
        pass


class TagCategory(object):
    """A TagCategory is for holding a collection of tags.
        the `category_name` is for informational purposes
        only.
    """
    def __init__(self, category_name):
        self.category_name = category_name
        self.tag_classes = set()

    def __repr__(self):
        return '{}({}: {})'.format(
            self.__class__.__name__,
            self.category_name,
            self.tag_classes,
        )

    def add_tag_cls(self, tag_cls):
        """Add a tag cls to this category.
            (returns `tag_cls` so could be used as a class decorator)
        """
        assert issubclass(tag_cls, BaseTag)
        for curr_tag_cls in self.tag_classes:
            if curr_tag_cls.tag_name == tag_cls.tag_name:
                raise ValueError(
                    "Cannot add {tag_cls} to tag category"
                    " '{self}' as name '{tag_cls.tag_name}'"
                    " clashes with tag {curr_tag_cls}."
                    .format(**locals()))

        self.tag_classes.add(tag_cls)

        return tag_cls

    def remove_tag_cls(self, tag_cls):
        """Remove a tag from the category.

        Args:
            tag_cls (BaseTag): the tag to remove
        """
        assert issubclass(tag_cls, BaseTag)
        try:
            self.tag_classes.remove(tag_cls)
        except KeyError:
            pass

    __call__ = add_tag_cls


@six.add_metaclass(BaseTagMeta)
class BaseTag(BaseNode):
    """Base class for representing BB Code tags to be used in a section of
    BB Code markup.

    These classes should not be initialized directly (are initialized by
    the parser).

    class attributes to be overwritten:
        `tag_name` - the string which is shown in the tag (e.g. [img] -> 'img')

        `close_on_newline` - wether to close on encountering a new line. e.g.
            "[b]Lorem Ipsum\\n"
                would be equivalent to
            "[b]Lorem Ipsum[/b]"

        `self_closing` - whether a tag needs to be closed, or is standalone.
            e.g. "[img ...]" is self closing, "[b]...[/b]" is not self closing.

        `allowed_tags` - The tags (or `TagCategory`s) which the tag will allow
            to be parsed within itself. Any (non consumable) iterable is
            accepted, e.g. list, tuple, set.

        `tag_categories` - The `TagCategory`s to which this tag belongs.

        `attr_defs` - definition of expected attributes as a dict in the form:
            {'attr_name': {<attr constraints>}}
                where 'attr_name' is the name of the attribute in the markup:
            [tagname attr_name="attr_val"]

            <attr constriants> are:
                `parser` - a callable which accepts one argument (the attr_val)
                    if not present in the dict, then attr_val is passed
                    through verbatim
                `default` - the default value to be returned if the attr is
                    not given in the markup. (N.B. it will not be put through
                    `parser`, and is returned as is).
                    if not present then the attr is considered required.

            an example attr_def is:
                attr_def = {
                    'banana_size': {'parser': int},
                    'apple_color': {'default': 'red'},
                }
            banana_size is required (no default) and the value will be passed
                through int before being returned.
            apple_color is not required, and defaults to 'red' if it's not
                given in the markup.

        `trim_whitespace` - whether to remove whitespace from either end of
            rendered text before returning it from render()

    Instance attributes which will be populated
        `self.tree` - a list of child tags/text

        `self.start_text` - the raw start text for the tag (including attrs)
            e.g. '[a]', or '[img src="bananas.com/pic.png"]'

        `self.end_text` - the raw end text for the tag.
            - if it is a self closing tag, this will be ''
            - if it is a tag closable by a newline, and has been, then this
              will be '\\n' (the offending newline)
            - else the close of the tag, e.g. "[/a]"

        `self.attrs` - a dictionary of {`attr_name`:`attr_val`}
            (see `attr_defs` above)

       `self.errors` - a list of strings denoting value errors with the tag.
            e.g. missing attrs, or attrs which failed to parse.

    Instancemethods to be overwritten:
        `_render` - function which takes no arguments, and returned the
            rendered version of the text.
    """
    tag_name = None

    close_on_newline = False
    self_closing = False

    allowed_tags = None
    tag_categories = []

    attr_defs = {}

    def __init__(self, attrs, tree, start_text, end_text):
        """These classes should not be initialized directly
            (are initialized by the parser).
        """
        assert self.self_closing is False or len(tree) == 0
        assert self.self_closing is False or end_text == ''
        super(BaseTag, self).__init__()
        self.tree = tree
        self.start_text = start_text
        self.end_text = end_text

        self.attrs, self.errors = self.parse_attrs(attrs)

        for node in self.tree:
            if isinstance(node, BaseNode):
                node.set_parent_node(self)

    def __eq__(self, other):
        return self.__class__ == other.__class__\
            and self.attrs == other.attrs\
            and self.tree == other.tree

    def __repr__(self):
        return '{}({}: {})'.format(
            self.__class__.__name__, self.tag_name, self.attrs
        )

    @classmethod
    def get_allowed_tags(cls):
        """returns the tags which are permitted within this tag,
            or None if not Specified
        """
        if cls.allowed_tags is None:
            return None

        return parse_tag_set(cls.allowed_tags)

    def pretty_format(self):
        """Return a human-readable formatted version of the tag instance,
            including tree
        """
        indent = ' ' * 4

        child_fmts = []
        for child in self.tree:
            child_fmts.append(
                getattr(child, 'pretty_format', child.__repr__)())

        fmt_child_list = '\n'.join(
            '{}{}'.format(indent, line)
            for child_text in child_fmts
            for line in child_text.split('\n')
        )

        if len(fmt_child_list):
            fmt_child_list = '\n' + fmt_child_list + '\n'

        return '{}({} tree({}) {} {})'.format(
            self.__class__.__name__, repr(self.start_text), fmt_child_list,
            repr(self.end_text), self.attrs
        )

    def find_children_instances(self, cls, multi=True):
        """This method searches immediate children for instances of `cls`
            if `multi` is truthy, then a list of found instances is returned.
            if `multi` is falsy, then only the last found instance is
                returned, and any extra instances found before hand are
                replaced with ErrorText.
                If no instance is found, `None` is returned.
        """
        if len(self.tree) == 0:
            return None

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

    def render_children(self):
        """Return the rendering of child tags/text
        """
        return ''.join(child.render() for child in self.tree)

    def _render(self):
        raise NotImplementedError

    def render_raw(self):
        """Return the raw text used to generate this tag,
            and all of its children.
        """
        return self.start_text + self.render_children_raw() + self.end_text

    def render_children_raw(self):
        """Return the raw text used to generate this tag's children.
        """
        return ''.join(child.render_raw() for child in self.tree)

    @classmethod
    def parse_attrs(cls, attrs):
        parsed_attrs = {}
        errors = []

        duplicate_keys = []

        for attr_key, attr_val in attrs:
            attr_def = cls.attr_defs.get(attr_key)

            if attr_def is None:
                errors.append('got undefined attr {}'.format(attr_key))
                continue

            if attr_key in parsed_attrs:
                duplicate_keys.append(attr_key)

            if 'parser' in attr_def:
                try:
                    attr_val = attr_def['parser'](attr_val)
                except ValueError as e:
                    errors.append(
                        'failed to parse attr {} with value {}: {}'.format(
                            attr_key, attr_val, e,
                        )
                    )
                    continue

            parsed_attrs[attr_key] = attr_val

        for key in duplicate_keys:
            errors.append('duplicate definition for key {}'.format(key))

        for attr_key, attr_def in cls.attr_defs.items():
            if attr_key not in parsed_attrs:
                try:
                    parsed_attrs[attr_key] = attr_def['default']
                except KeyError:
                    errors.append(
                        'missing required attr {}'.format(attr_key)
                    )

        return parsed_attrs, errors



class RootTag(BaseTag):

    def _render(self, ctx=None):
        return self.render_children()


class SimpleTag(BaseTag):
    # use one '{{ body }}' to be replaced with the contents
    # of the items children
    # e.g. "<awesometext>{{ body }}</awesometext>"
    template = None
    replace_text = '{{ body }}'

    def _render(self):
        if self.template is None:
            return self.render_children()

        return self.template.replace(
            self.replace_text, self.render_children()
        )


def parse_tag_set(tag_set):
    """Tag sets are iterables of BaseTag subclasses and TagCategories
        This function flattens the given tag_set to a list of tag classes
    """
    tags = set()
    for tag in tag_set:
        if isinstance(tag, TagCategory):
            tags.update(tag.tag_classes)

        elif issubclass(tag, BaseTag):
            tags.add(tag)

        else:
            raise TypeError(
                "Unknown object passed to parse_tag_set: (type {}) {}".format(
                    type(tag), tag
                )
            )

    # check for duplicate tag names
    seen = set()
    for tag in tags:
        if tag.tag_name in seen:
            raise ValueError(
                "Duplicate tag names detected: {}".format(tag.tag_name))
        seen.add(tag.tag_name)

    return tags
