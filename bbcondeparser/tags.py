import six

from bbcondeparser.utils import escape_html
from bbcondeparser.errors import BBCondeParseError


class BaseText(object):
    """This class is to hold chunks of plain text. This
        class handles escaping html within the text.
    """
    def __init__(self, text):
        self.text = text

    def render(self, escape=True):
        text = self.get_raw()

        if escape:
            text = escape_html(text)

        return text

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, repr(self.get_raw()))

    def get_raw(self):
        return self.text

    def render_raw(self):
        return self.render()


class RawText(BaseText):
    pass


class ErrorText(BaseText):
    def __init__(self, text, reason=None):
        super(ErrorText, self).__init__(text)
        self.reason = reason

    def __repr__(self):
        return "{}('{}': {})".format(
            self.__class__.__name__, self.reason, repr(self.get_raw()),
        )


class BaseTagMeta(type):
    def __new__(cls, name, bases, ctx):
        def render(self):
            return self.render_children()

        null_name = 'Null{}'.format(name)
        null_ctx = dict(ctx)
        null_ctx['render'] = render
        new_null_cls = super(BaseTagMeta, cls).__new__(
                cls, null_name, bases, null_ctx)

        new_cls = super(BaseTagMeta, cls).__new__(cls, name, bases, ctx)

        new_cls.null_class = new_null_cls
        new_null_cls.null_class = new_null_cls

        return new_cls


@six.add_metaclass(BaseTagMeta)
class BaseTag(object):
    # These attributes are for the parsers to discern behavour.
    tag_name = None # what goes between the []s
    close_on_newline = False
    self_closing = False # Should it be [a ...]..[/a] or just [img ...]?

    # if the tag has a specific set of tags it expects inside of itself,
    # then define them here. (e.g. for infobox and its items)
    tag_set = None

    # defines what attributes are allowed, their parsers and default values.
    # required attributes should not define a third option for default
    attr_defs = {}
    # e.g.
    # attrs = {
    #   'banana_size': {'parser': int}, # required attr called banana_size, parsed using int()
    #   'apple_color': {'default': 'red'}, # optional attr called apple_color, defaults to 'red'
    # }

    # These attributes are about the formating of output text
    #TODO implement convert_newlines, remove_paragraphs
    convert_newlines = False # change newlines to <br/>
    remove_paragraphs = False # removes <p> from content
    trim_whitespace = False

    def __init__(self, attrs, tree, start_text, end_text):
        assert self.self_closing is False or len(tree) == 0
        assert self.self_closing is False or end_text == ''
        self.tree = tree
        self.start_text = start_text
        self.end_text = end_text

        self._errors = []
        self.parse_attrs(attrs)

    def __repr__(self):
        return '{}({}: {})'.format(
            self.__class__.__name__, self.tag_name, self.attrs
        )

    def pretty_print(self):
        indent = ' ' * 4

        child_fmts = []
        for child in self.tree:
            child_fmts.append(getattr(child, 'pretty_print', child.__repr__)())

        fmt_child_list = '\n'.join(
            '{}{}'.format(indent, line)
            for child_text in child_fmts
            for line in child_text.split('\n')
        )

        if len(fmt_child_list):
            fmt_child_list = '\n' + fmt_child_list + '\n'

        return '{}({} tree({}) {} {{{}}})'.format(
            self.__class__.__name__, self.start_text, fmt_child_list,
            self.end_text, self.attrs
        )

    def parse_attrs(self, attrs):
        self.attrs = parsed_attrs = {}

        duplicate_keys = []

        for attr_key, attr_val in attrs:
            attr_def = self.attr_defs.get(attr_key)

            if attr_def is None:
                self._errors.append('got undefined attr {}'.format(attr_key))
                continue

            if attr_key in parsed_attrs:
                duplicate_keys.append(attr_key)

            if 'parser' in attr_def:
                try:
                    attr_val = attr_def['parser'](attr_val)
                except ValueError as e:
                    self._errors.append(
                        'failed to parse attr {} with value {}: {}'.format(
                        attr_key, attr_val, e,
                        )
                    )
                    continue

            parsed_attrs[attr_key] = attr_val

        for key in duplicate_keys:
            self._errors.append('duplicate definition for key {}'.format(key))

        for attr_key, attr_def in self.attr_defs.items():
            if attr_key not in parsed_attrs:
                try:
                    parsed_attrs[attr_key] = attr_def['default']
                except KeyError:
                    self._errors.append(
                        'missing required attr {}'.format(attr_key)
                    )

    def render_children(self):
        return ''.join(child.render() for child in self.tree)

    def render(self):
        text = self._render()

        if self.trim_whitespace:
            text = text.strip()

        return text

    def _render(self):
        raise NotImplementedError

    def render_raw(self):
        return self.start_text + self.get_children_raw()  + self.end_text

    def get_children_raw(self):
        return ''.join(child.render_raw() for child in self.tree)


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
