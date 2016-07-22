from bbcondeparser.utils import escape_html
from bbcondeparser.errors import BBCondeParseError

class REQUIRED(object): pass


class BaseText(object):
    def __init__(self, text):
        self.text = text

    def render(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, repr(self.get_raw()))

    def get_raw(self):
        return self.text


class RawText(BaseText):
    """This class is to hold chunks of plain text. This
        class handles escaping html within the text.
    """
    def render(self, escape=True):
        text = self.get_raw()

        if escape:
            text = escape_html(text)

        return text


class ErrorText(BaseText):
    def __init__(self, text, reason=None):
        super(ErrorText, self).__init__(text)
        self.reason = reason

#    def __repr__(self):
#        #HERE TODO

    def render(self):
        return self.get_raw()


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
    attr_defs = tuple()
    # e.g.
    # attrs = (
    #   ('banana_size', int), # required attr called banana_size, parsed using int()
    #   ('apple_color', None, 'red'), # optional attr called apple_color, defaults to 'red'
    # )

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

        self.attrs = self.parse_attrs(attrs)

    def __repr__(self):
        return '{}({}: {})'.format(
            self.__class__.__name__, self.tag_name, self.attrs
        )

    @classmethod
    def parse_attrs(cls, attrs):
        given_attrs = dict(attrs)
        parsed_attrs = {}

        for attr_def in cls.attr_defs:
            attr_name, parser = attr_def[:2]
            default = attr_def[2] if len(attr_def) == 3 else REQUIRED

            # TODO better messages on failures
            val = given_attrs.pop(attr_name, default)

            if val is REQUIRED:
                raise BBCondeParseError(
                        '{} is is a required attribute for {}'.format(
                        cls.attr_name, cls.tag_name))

            parsed_val = parser(val) if parser is not None else val
            parsed_attrs[attr_name] = parsed_val

        #TODO finish this
        return parsed_attrs

    def render_children(self):
        return ''.join(child.render() for child in self.tree)

    def render(self):
        text = self._render()

        if self.trim_whitespace:
            text = text.strip()

        return text

    def _render(self):
        raise NotImplementedError

    def get_raw(self):
        return self.start_text + self.get_children_raw()  + self.end_text

    def get_children_raw(self):
        return ''.join(child.get_raw() for child in self.tree)

class BaseSimpleTag(BaseTag):
    # use one '{{ body }}' to be replaced with the contents
    # of the items children
    # e.g. "<awesometext>{{ body }}</awesometext>"
    template = None
    replace_text = '{{ body }}'
    def _render(self):
        if self.template is None:
            raise RuntimeError(
                    "{} class has no template defined".format(
                    self.__class__.__name__))

        return self.template.replace(self.replace_text, self.render_children())

###############################################################################
# Tag definitions
###############################################################################
class CodeTag(BaseTag):
    tag_name = 'code'
    def _render(self):
        return '<pre><code>{}</code></pre>'.format(self.get_children_raw())


class BoldTag(BaseSimpleTag):
    tag_name = 'b'
    template = '<strong>{{ body }}</strong>'
