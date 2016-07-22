import sys
import re

def normalize_newlines(text):
    """Tidies up newlines in the block of text
    \r = CR (Carriage Return) - Used as a new line character in Mac OS before X
    \n = LF (Line Feed) - Used as a new line character in Unix/Mac OS X
    \r\n = CR + LF - Used as a new line character in Windows
    """
    # Replace all single \r with \n
    transformed_text = text.replace('\r[^\n]', '\n')
    # Replace all \r\n newlines with \n
    # \r\n is a single newline on windows
    transformed_text = transformed_text.replace('\r\n', '\n')
    # Replace any \n\n\n+ into just twos
    transformed_text = re.sub(r'\n{3,}', '\n\n', transformed_text)
    return transformed_text


# Dan wanted this in here... He says it's "performant"
def trim_whitespace(text, whitespace=False):
    '''
    This function trims the whitespace from some text. You pass it text and it
    removes it. For example:
    butts  to butts
    '''
    def _ltrim(text):
        '''This removes the left whitespace from text'''
        return text.lstrip()

    def _rtrim(text):
        '''This removes the right whitespace from text'''
        return text.tstrip()

    if not whitespace:
        return text

    return '{z}'.format(z=_rtrim('%s' % _ltrim(text)))


if sys.version_info.major == '2':
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
    #TODO
    return text