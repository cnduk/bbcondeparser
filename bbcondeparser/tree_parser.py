import re

from bbcondeparser.utils import (
    to_unicode, normalize_newlines, remove_backslash_escapes
)
from bbcondeparser.tags import ErrorText, RawText, parse_tag_set

TAG_START = 'tag_start'
TAG_END = 'tag_end'


class BaseTreeParser(object):
    tags = []
    ignored_tags = []

    raw_text_class = RawText
    error_text_class = ErrorText

    def __init__(self, text):
        self.raw_text = text

        ignored_tags = [tag.null_class for tag in self.ignored_tags]
        tags = self.tags + ignored_tags

        self.tree = parse_tree(
            text, tags,
            raw_text_class=self.raw_text_class,
            error_text_class=self.error_text_class
        )


    def render(self):
        return ''.join(tag.render() for tag in self.tree)

    def pretty_format(self):
        return '\n'.join(
            getattr(child, 'pretty_format', child.__repr__)()
            for child in self.tree
        )


def parse_tree(
    raw_text, tags, raw_text_class=RawText, error_text_class=ErrorText,
):
    """`raw_text` is the raw bb code (conde format) to be parsed
        `tags` should be an iterable of tag classes allowed in the text
    """
    raw_text = to_unicode(raw_text)
    raw_text = normalize_newlines(raw_text)
    tag_dict = create_tag_dict(tags)

    stack = [] # stack of (tree, tag_dict, tag_cls, tag_attrs, tag_open_text)
    tree = []

    curr_pos = 0
    while curr_pos < len(raw_text):
        last_pos = curr_pos

        if stack and stack[-1][2].close_on_newline:
            curr_pos = find_next_multi_char(raw_text, '[\n', curr_pos)

        else:
            curr_pos = raw_text.find('[', curr_pos)

        if curr_pos == -1:
            # No more open/close tags
            tree.append(raw_text_class(raw_text[last_pos:]))
            break

        if curr_pos > last_pos: # We've scanned past some text
            tree.append(raw_text_class(raw_text[last_pos:curr_pos]))

        if stack and stack[-1][2].close_on_newline and raw_text[curr_pos] == '\n':
            tag_tree = tree

            tree, tag_dict, tag_cls, tag_attrs, tag_text = stack.pop()
            tree.append(tag_cls(tag_attrs, tag_tree, tag_text, '\n'))
            curr_pos += 1

            continue


        #TODO disallow newlines in middle of tags?
        next_close = raw_text.find(']', curr_pos)
        if next_close == -1:
            tree.append(error_text_class(
                raw_text[curr_pos:], "Missing tag close ']'"
            ))
            break

        else:
            tag_info = parse_tag(raw_text[curr_pos+1:next_close])
            if tag_info is None:
                tree.append(error_text_class(
                    raw_text[curr_pos:next_close+1], "Invalid tag syntax"
                ))
                curr_pos = next_close + 1
                continue

            tag_open_close, tag_name, tag_attrs = tag_info
            tag_cls = tag_dict.get(tag_name, None)

            if tag_cls is None and (not stack or stack[-1][2].tag_name != tag_name):
                tree.append(error_text_class(
                    raw_text[curr_pos:next_close+1], "unknown tag"
                ))
                curr_pos = next_close + 1
                continue

            if tag_cls is not None and tag_open_close == TAG_START:
                if tag_cls.self_closing:
                    tree.append(tag_cls(tag_attrs, [], raw_text[curr_pos:next_close+1], ''))
                    curr_pos = next_close + 1
                    continue

                stack.append((
                    tree, tag_dict, tag_cls, tag_attrs,
                    raw_text[curr_pos: next_close+1]
                ))
                tree = []

                tag_dict = get_new_tag_dict(tag_cls, tag_dict)

                curr_pos = next_close + 1
                continue


            # tag_open_close == TAG_END
            if not stack or tag_name != stack[-1][2].tag_name:
                tree.append(error_text_class(
                    raw_text[curr_pos:next_close+1],
                    "Close tag does not match current open tag '{}'".format(
                        (stack[-1][2].tag_name if stack else '<None>'),
                    )
                ))
                curr_pos = next_close + 1
                continue

            tag_tree = tree
            tree, tag_dict, tag_cls, tag_attrs, tag_text = stack.pop()

            tree.append(tag_cls(tag_attrs, tag_tree, tag_text, raw_text[curr_pos:next_close+1]))
            curr_pos = next_close + 1

    while stack:
        # Things have gone wrong here, there are un-closed tags.
        curr_tree = tree
        tree, tag_dict, tag_cls, tag_attrs, tag_text = stack.pop()

        tree = tree + [error_text_class(tag_text, "Missing close tag")] + curr_tree

    return tree


_whitespace_re = re.compile('\s+')

_tag_name_re_str = '[a-zA-Z-]+'
_end_tag_re = re.compile('^/{_tag_name_re_str}$'.format(**locals()))
_start_tag_name_re = re.compile('^{_tag_name_re_str}$'.format(**locals()))

_attr_re_str = r'([a-zA-Z-]+)="((?:[^\\"]|\\.)*)"'
_attr_re = re.compile(_attr_re_str)
_attrs_re = re.compile(r'^(?:\s*{_attr_re_str}\s*)*$'.format(**locals()))

def parse_tag(text):
    """`text` should be the text from within the tag
        e.g:
        [img src="banana.com/pic"] = img src="banana.com/pic"
        [b] = b
        [/b] = /b

        returns a tuple (start/end, name, attrs)
            `start/end` is either tree_parser.TAG_START or tree_parser.TAG_END,
                indicating if it's a starting tag or end tag.
            `name` is the name of the tag
            `attrs` is any attributes defined as a tuple of two-tuples
                (on an open tag only, None on end tags)
        returns None on a failed parse
    """
    if not text: # tag was empty (e.g. [])
        return None

    if text[0] == '/': # It's a close tag e.g. [/foo]
        if _end_tag_re.match(text):
            return (TAG_END, text[1:], None)
        else:
            return None

    # [tagname<whitespace><attrs...>] -> (<tagname>, <attrs...>)
    # or [tagname] -> (<tagname>,)
    # or [tagname<whitespace>] -> (tagname, '')
    parts = _whitespace_re.split(text, maxsplit=1)
    tag_name = parts[0]
    attrs_str = parts[1] if len(parts) == 2 else ''

    if not (_start_tag_name_re.match(tag_name) and _attrs_re.match(attrs_str)):
        return None

    attr_vals = list(
        (attr_name, remove_backslash_escapes(attr_val))
        for attr_name, attr_val in _attr_re.findall(attrs_str)
    )

    return (TAG_START, tag_name, tuple(attr_vals))


def create_tag_dict(tags):
    # parse_tag_set will raise a RuntimeError
    # if duplicate tag_names are detected.
    tags = parse_tag_set(tags)
    return {tag.tag_name: tag for tag in tags}


def get_new_tag_dict(tag_cls, tag_dict):
    allowed_tags = tag_cls.get_allowed_tags()
    if allowed_tags is not None:
        tag_dict = {
            tag_name: tag_cls.null_class
            for tag_name, tag_cls in tag_dict.items()
        }
        tag_dict.update(create_tag_dict(tag_cls.allowed_tags))

    return tag_dict


def find_next_multi_char(search_string, chars, start=0):
    # So I thought this would be inefficient, and tried to improve it.
    # I did some benchmarking and for small numbers of `chars` (which we'll
    # be using in this module) it makes little difference whether we
    # try and combine multiple str.find()s, or loop through the string
    # ourselves to try and locate the next character.
    matches = list(
        match
        for match in (
            search_string.find(char, start)
            for char in chars
        )
        if match >= 0
    )

    return min(matches) if matches else -1