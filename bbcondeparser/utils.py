import sys
import re
import cgi


if sys.version_info.major == 2:
    def to_unicode(string_like_object):
        """Convert the item to unicode, so we're dealing
            with characters and not bytes.
        """
        if isinstance(string_like_object, unicode):
            return string_like_object
        else:
            #TODO might need to be more resilient, rather than just rely
            # on the data being utf-8 compatible
            return string_like_object.decode('utf-8')
else:
    def to_unicode(string_like_object):
        """With python>=3, this function does nothing
        """
        return string_like_object


def escape_html(text):
    return cgi.escape(text, quote=True)


_backslash_sub_re = re.compile(r'(\\.)')
def _replace_backslash_sub(match):
    # our regex will only match 2 characters, a backslash and some character
    # we just want to replace the two characters with whatever the second character is.
    return match.groups()[0][1]


def remove_backslash_escapes(text):
    return _backslash_sub_re.sub(_replace_backslash_sub, text)


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


def strip_newlines(text, newline_char='\n'):
    """Removes any newline characters from the text
    """

    return text.replace(newline_char, '')


def convert_newlines(text, newline_char='\n', convert_char='<br />'):
    """Converts the new line character into the convert character
    """

    return text.replace(newline_char, convert_char)
