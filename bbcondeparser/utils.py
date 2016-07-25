import sys
import re
import cgi

_normalize_multi_newlines_re = re.compile('\n{3,}')
def normalize_newlines(text):
    """Tidies up newlines in the block of text
    \r = CR (Carriage Return) - Used as a new line character in Mac OS before X
    \n = LF (Line Feed) - Used as a new line character in Unix/Mac OS X
    \r\n = CR + LF - Used as a new line character in Windows
    """
    # Replace all \r\n newlines with \n
    # \r\n is a single newline on windows
    transformed_text = text.replace('\r\n', '\n')

    # Replace any \n\n\n+ into just twos
    transformed_text = _normalize_multi_newlines_re.sub('\n\n', transformed_text)
    return transformed_text


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
        """Under python>=3, this function does nothing
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