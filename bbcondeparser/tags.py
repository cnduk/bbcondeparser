from bbcondeparse.errors import BBCondeParseError

class REQUIRED(object): pass

def escape_html(text):
    #TODO
    return text

class RawText(object):
    """This class is to hold chunks of plain text. This
        class handles escaping html within the text.
    """
    def __init__(self, text):
        self.text = text

    def render(self, escape_html=True):
        if escape_html:
            return escape_html(self.text)
        else:
            return self.text

    # TODO need to detect URLs and put some html on them?
    # See "dangling_links" from original bb code parser.
    # Dan seems to think they've gone

class ErrorText(object):
    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text

class BaseTag(object):
    # These attributes are for the parsers to discern behavour.
    tag_name = None # what goes between the []s
    close_on_newline = False
    self_closing = False # Should it be [img ...] or [a]..[/a]?
    dont_parse_contents = False # Just give tree as single RawText

    # if the tag has a specific set of tags it expects inside of itself,
    # then define them here. (e.g. for infobox and its items)
    tag_set = {}

    # defines what attributes are allowed, their parsers and default values.
    # required attributes should not define a third option for default
    attrs = tuple()
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

    def __init__(self, attrs, tree):
        self.tree = tree

        self.attrs = self.parse_attrs(attrs)

    @classmethod
    def parse_attrs(cls, attrs):
        given_attrs = dict(attrs)
        parsed_attrs = {}

        for attr_def in cls.attrs:
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

    def render_children(self):
        return ''.join(child.render() for child in self.tree)

    def render(self):
        text = self._render()

        if self.trim_whitespace:
            text = text.strip()

        return text

    def _render(self):
        raise NotImplementedError


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
    dont_parse_contents = True


class BoldTag(BaseSimpleTag):
    tag_name = 'b'
    template = '<strong>{{ body }}</strong>'
