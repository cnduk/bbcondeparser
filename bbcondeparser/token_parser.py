import re

from bbcondeparser.utils import (
    to_unicode, remove_backslash_escapes, find_next_multi_char
)

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


class CloseTagToken(BaseToken):
    def __init__(self, text, location, tag_name):
        super(CloseTagToken, self).__init__(text, location)
        self.tag_name = tag_name


class TokenParser(object):
    def __init__(self, raw_text):
        self.original_text = raw_text
        self.text = to_unicode(raw_text)

        self.parse_tokens()

    def parse_tokens(self):
        self.tokens = []
        self.curr_pos = 0

        search_chars = NEWLINE_CHARS + u'['

        while self.curr_pos < len(self.text):
            self.last_pos = self.curr_pos
            self.curr_pos = find_next_multi_char(
                    self.text, search_chars, self.curr_pos)

            # If we've moved past characters other than our search characters,
            # Then that's just plain text.
            # (if curr_pos is -1 (notfound) this is skipped)
            if self.last_pos < self.curr_pos:
                self.add_text_token(
                    self.text[self.last_pos:self.curr_pos],
                    (self.last_pos, self.curr_pos),
                )

            # Reached the end of the text. We know that we have scanned past
            # some text because of the while clause.
            if self.curr_pos == -1:
                self.curr_pos = len(self.text)
                location = (self.last_pos, self.curr_pos)
                self.add_text_token(
                    self.text[self.last_pos:self.curr_pos], location
                )

            elif self.text[self.curr_pos] == '[':
                self.parse_tag_token()

            # self.text[self.curr_pos] in NEWLINE_CHARS:
            else:
                self.process_newline()


            # Move onto next character to start processing from
            self.curr_pos += 1

    def add_text_token(self, text, location):
        self.tokens.append(TextToken(text, location))

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
        assert self.text[self.curr_pos] == '['

        end_of_tag_loc = find_next_multi_char(
                self.text, '][', self.curr_pos+1)

        if end_of_tag_loc == -1 or self.text[end_of_tag_loc] == '[':
            if end_of_tag_loc == -1:
                end_of_tag_loc = len(self.text)-1
            else:
                # Need to step back a character so that the '[' will
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
_attr_re_str = r'([a-zA-Z-]+)="((?:[^\\"]|\\.)*)"'
_attrs_re_str = r'^(?:\s*{_attr_re_str}\s*)*$'.format(**locals())

_close_tag_re = re.compile('^/{_tag_name_re_str}\s*$'.format(**locals()))
_start_tag_name_re = re.compile('^{_tag_name_re_str}$'.format(**locals()))

_attr_re = re.compile(_attr_re_str)
_attrs_re = re.compile(_attrs_re_str)

_salvage_re = re.compile(
        r'(\[/?(:?{_tag_name_re_str}(\s{_attr_re_str})*)?)'.format(**locals()))

def salvage_tag_offset(text):
    """`text` should be everything from the open [
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
    assert text[0] == '['

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
    assert text[0] == '[' and text[-1] == ']'
    text = text[1:-1]

    if not text: # tag was empty (e.g. [])
        return None

    if text[0] == '/': # It's a close tag e.g. [/foo]
        if _close_tag_re.match(text):
            return ('close_tag', text[1:], None)
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

    return ('open_tag', tag_name, tuple(attr_vals))
