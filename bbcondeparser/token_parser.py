# Copyright (c) 2017 Conde Nast Britain
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from collections import Mapping

from bbcondeparser.utils import (
    to_unicode, remove_backslash_escapes, find_next_multi_char,
    add_backslash_escapes,
)

OPEN_CHAR = u'['
CLOSE_CHAR = u']'

# N.B. This creates a unicode/string!
NEWLINE_CHARS = (
    '\n' # LF - Line Feed
    '\r' # CR - Carriage Return
    '\v' # VT - Vertical Tab
    '\f' # FF - Form Feed
    u'\u2029' # Paragraph separator
    u'\u2028' # Line separator
    # u'\u0085' # NEL - NExt Line. Ignored because it's not common,
                # and Windows uses it as an elipsis.
    # DOS newlines \r\n are special cased in the parser.
)


def get_tokens(text):
    parser= TokenParser(text)
    return parser.tokens


class BaseToken(object):
    """An object to represent a token within the source text
    """
    def __init__(self, text, location):
        """loc is the location in the text the token is from.
            It is given to this class to make it accesible later on,
            but it not used by this class.
            (exposed via self.location)
        """
        self.text = text
        self.location = location

    def __repr__(self):
        return '{}({}@{})'.format(
            self.__class__.__name__,
            repr(getattr(self, 'text', '<UNINITIALIZED!!>')),
            getattr(self, 'location', '<UNINITIALIZED!!>'),
        )

    def __eq__(self, other):
        return self.__class__ is other.__class__ \
                and self.text == other.text \
                and self.location == other.location


class TextToken(BaseToken):
    pass


class BadSyntaxToken(BaseToken):
    def __init__(self, text, location, reason):
        super(BadSyntaxToken, self).__init__(text, location)
        self.reason = reason


class NewlineToken(BaseToken):
    pass


class OpenTagToken(BaseToken):
    def __init__(self, text, location, tag_name, attrs):
        super(OpenTagToken, self).__init__(text, location)
        self.tag_name = tag_name
        self.attrs = attrs

    def __repr__(self):
        return '{}({}@{}<{}@{}>)'.format(
            self.__class__.__name__,
            repr(getattr(self, 'text', '<UNINITIALIZED!!>')),
            getattr(self, 'location', '<UNINITIALIZED!!>'),
            getattr(self, 'tag_name', '<UNINITIALIZED!!>'),
            getattr(self, 'attrs', '<UNINITIALIZED!!>'),
        )

    def __eq__(self, other):
        return super(OpenTagToken, self).__eq__(other) \
            and self.tag_name == other.tag_name \
            and self.attrs == other.attrs

    @classmethod
    def generate_token(cls, start_location, tag_name, attrs):
        """ Tool to generate text for an open tag based on its attributes.
            This will return an instance with `text` populated with
            the appropriate string.

            args:
                `location` - the index of the first character where this tag
                    will be inserted.
                `tag_name` - string for the tag name. e.g. if you want
                    '[img src="https://example.com/image.png"]'
                    `tag_name` = 'img'
                `attrs` - an iterable of two-tuple (or other unpackable things
                    of length 2). This function handles escaping.
                    will also accept a dict, (will order attrs)
        """
        tag_name = to_unicode(tag_name)

        if not attrs:
            attr_text = ''

        else:
            if isinstance(attrs, (dict, Mapping)):
                attrs = sorted(attrs.items())

            attrs = tuple((
                (to_unicode(str(name)), to_unicode(str(val)))
                for name, val in attrs
            ))

            # need to put a space between the name and the attrs
            attr_text = ' ' + ' '.join(
                '{}="{}"'.format(k, add_backslash_escapes(v))
                for k, v in attrs
            )

        text = '[' + tag_name + attr_text + ']'
        location = (start_location, start_location+len(text))
        return cls(text, location, tag_name, attrs)


class CloseTagToken(BaseToken):
    def __init__(self, text, location, tag_name):
        super(CloseTagToken, self).__init__(text, location)
        self.tag_name = tag_name

    def __eq__(self, other):
        return super(CloseTagToken, self).__eq__(other) \
            and self.tag_name == other.tag_name


class TokenParser(object):
    def __init__(self, raw_text):
        self.original_text = raw_text
        self.text = to_unicode(raw_text)

        self.parse_tokens()

    def parse_tokens(self):
        self.tokens = []
        self.curr_pos = 0

        search_chars = NEWLINE_CHARS + OPEN_CHAR

        while self.curr_pos < len(self.text):
            self.last_pos = self.curr_pos
            self.curr_pos = find_next_multi_char(
                    self.text, search_chars, self.curr_pos)

            # If we've moved past characters other than our search characters,
            # Then that's just plain text.
            # (if curr_pos is -1 (notfound) this is skipped)
            if self.last_pos < self.curr_pos:
                self.add_text_token()

            # Reached the end of the text. We know that we have scanned past
            # some text because of the while clause.
            if self.curr_pos == -1:
                self.curr_pos = len(self.text)
                self.add_text_token()

            elif self.text[self.curr_pos] == OPEN_CHAR:
                self.parse_tag_token()

            # self.text[self.curr_pos] in NEWLINE_CHARS:
            else:
                self.process_newline()

            # Move onto next character to start processing from
            self.curr_pos += 1

    def add_text_token(self):
        self.tokens.append(TextToken(
            self.text[self.last_pos:self.curr_pos],
            (self.last_pos, self.curr_pos),
        ))

    def process_newline(self):
        assert self.text[self.curr_pos] in NEWLINE_CHARS

        char = self.text[self.curr_pos]
        location = (self.curr_pos, self.curr_pos+1)

        # either it's a dos newline \r\n, so need to consume two characters,
        # or it's just a single \n, \r or a newfangled unicode character.
        # Note \n\r is not a dos newline, it is a 'nix and mac newline.
        if char == '\r':
            try:
                next_char = self.text[self.curr_pos+1]
            except IndexError:
                next_char = None

            if next_char == '\n':
                # woo we've found a dos newline! so consume the next
                # character as well.
                char += next_char
                location = (self.curr_pos, self.curr_pos+2)
                self.curr_pos += 1

        self.tokens.append(NewlineToken(char, location))

    def parse_tag_token(self):
        assert self.text[self.curr_pos] == OPEN_CHAR

        end_of_tag_loc = find_next_multi_char(
                self.text, OPEN_CHAR+CLOSE_CHAR, self.curr_pos+1)

        if end_of_tag_loc == -1 or self.text[end_of_tag_loc] == OPEN_CHAR:
            if end_of_tag_loc == -1:
                end_of_tag_loc = len(self.text)-1
            else:
                # Need to step back a character so that the OPEN_CHAR will
                # be processed by the main loop
                end_of_tag_loc -= 1

            recover_offset = salvage_tag_offset(
                self.text[self.curr_pos:end_of_tag_loc+1]
            )
            # Backtrack so that the main loop can process the
            # leftover text. N.B. recover_offset is the location
            # of the first character of the recovered text,
            # so that's why there's a -1 to the value here.
            # (at the end of parse_tokens, have to leave curr_pos
            # pointing to the last character consumed)
            end_of_tag_loc = (self.curr_pos + recover_offset) - 1

            self.tokens.append(BadSyntaxToken(
                self.text[self.curr_pos:end_of_tag_loc+1],
                (self.curr_pos, end_of_tag_loc+1),
                "Missing tag closing character",
            ))

        else:
            tag_text = self.text[self.curr_pos:end_of_tag_loc+1]
            tag_location = (self.curr_pos, end_of_tag_loc+1)
            tag_info = parse_tag(tag_text)

            if tag_info is None:
                self.tokens.append(BadSyntaxToken(
                    tag_text, tag_location, "Bad tag syntax"
                ))

            else:
                tag_type, tag_name, tag_attrs = tag_info

                if tag_type == 'open_tag':
                    self.tokens.append(OpenTagToken(
                        tag_text, tag_location, tag_name, tag_attrs
                    ))

                else: # tag_type == 'close_tag'
                    self.tokens.append(CloseTagToken(
                        tag_text, tag_location, tag_name
                    ))

        self.curr_pos = end_of_tag_loc


_whitespace_re = re.compile('\s+')

_tag_name_re_str = '[\w-]+'
_attr_re_str = r'([a-zA-Z-]+)=("(?:[^\\"]|\\.)*"|\'(?:[^\\\']|\\.)*\')'
_attrs_re_str = r'^(?:\s*{_attr_re_str}\s*)*$'.format(**locals())

_close_tag_re = re.compile('^/({_tag_name_re_str})\s*$'.format(**locals()))
_start_tag_name_re = re.compile('^{_tag_name_re_str}$'.format(**locals()))

_attr_re = re.compile(_attr_re_str)
_attrs_re = re.compile(_attrs_re_str)

_salvage_re = re.compile(
        r'(\[/?(:?{_tag_name_re_str}(\s{_attr_re_str})*)?)'.format(**locals()))

def salvage_tag_offset(text):
    """`text` should be everything from the OPEN_CHAR
        e.g. if you've one of the following:
            '[boldLorem Ipsum dolor sit [i]amet[/i]'
            '[link loc="www.bananas.com/pic.png" Bananas are the best![/link]'
            '[/bold I have a lovely bunch of coconuts' (EOF)
        then this function takes the beginning part
            '[boldLorem Ipsum dolor sit '
            '[link loc="www.bananas.com/pic.png" Bananas are the best!'
            '[/bold I have a lovely bunch of coconuts'
        and find the point at which it believes the tag ends
            '[boldLorem' /offset 10/  'Ipsum dolor sit '
            '[link loc="www.bananas.com/pic.png"' /offset 34/ ' Bananas are the best!'
            '[/bold' /offset 6/ ' I have a lovely bunch of coconuts'

        returns the offset from the beginning of `text` from
        which text should be salvaged.
    """
    assert text[0] == OPEN_CHAR

    match = _salvage_re.match(text)
    return len(match.groups()[0])


def parse_tag(text):
    """`text` should be the complete text for the tag
        e.g:
        [img src="banana.com/pic"]
        [b]
        [/b]

        returns a tuple (start/end, name, attrs)
            `start/end` is either open_tag or close_tag
                indicating if it's a starting tag or end tag.
            `name` is the name of the tag
            `attrs` is any attributes defined as a tuple of two-tuples
                (on an open tag only, None on end tags)
        returns None on a failed parse
    """
    assert text[0] == OPEN_CHAR and text[-1] == CLOSE_CHAR
    text = text[1:-1]

    if not text: # tag was empty (e.g. [])
        return None

    if text[0] == '/': # It's a close tag e.g. [/foo]
        match = _close_tag_re.match(text)
        if match:
            return ('close_tag', match.groups()[0], None)
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

    attr_vals = tuple(
        (attr_name, remove_backslash_escapes(attr_val[1:-1]))
        for attr_name, attr_val in _attr_re.findall(attrs_str)
    )

    return ('open_tag', tag_name, attr_vals)
