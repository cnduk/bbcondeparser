import re

from bbcondeparser.utils import to_unicode, normalize_newlines


TAG_START = 'tag_start'
TAG_END = 'tag_end'


def parse_tree(raw_text, tags):
    """`raw_text` is the raw bb code (conde format) to be parsed
        `tags` should be an iterable of tag classes allowed in the text
    """
    raw_text = to_unicode(raw_text)
    raw_text = normalize_newlines(raw_text)
    tag_dict = create_tag_dict(tags)
    

    stack = []
    tree = []

    curr_pos = 0
    while curr_pos < len(raw_text):
        pass


_attr_name_re_str = '[a-zA-Z-]+'
_whitespace_re = re.compile('\s*')
# end tags should just be a / and tag name
_end_tag_re = re.compile('^/{_attr_name_re_str}$'.format(locals()))
_attr_re_str = ( # <attr_name>="<attr_val>"
    r'{_attr_name_re_str}' # <attr_name>
    r'="' # ="
    r'(?:(?:[^\\"]|\\.)*)' # Inbetween the "s, can have anything which isn't
    r'"' # "
).format(locals())
def parse_tag(text):
    """`text` should be the text from within the tag
        e.g:
        [img src="banana.com/pic"] = img src="banana.com/pic"
        [b] = b
        [/b] = /b

        returns a tuple (start/end, name, attrs)
            start/end is either parser.TAG_START or parser.TAG_END,
                indicating if it's a starting tag or end tag.
            name is the name of the tag
            attrs is any attributes defined
                (on an open tag only, None on end tags)
        returns None on a failed parse
    """
    if text[0] == '/':
        if _end_rag_re.match(text[1:]):
            return (TAG_END, text[1:], None)
        else:
            return None

    parts = _whitespace_re.split(text, maxsplit=1)
    tag_name = parts[0]
    attrs = parts[1] if len(parts) == 2 else ''



def create_tag_dict(tags):
    tag_dict = {
        tag.tag_name: tag
        for tag in tags
    }

    if len(tags) != len(tag_dict):
        raise RuntimeError("Duplicate tag names detected")

    return tag_dict