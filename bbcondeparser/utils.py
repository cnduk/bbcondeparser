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

import sys
import re


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


_backslash_sub_re = re.compile(r'(\\.)')
def _replace_backslash_sub(match):
    # our regex will only match 2 characters, a backslash and some character
    # we just want to replace the two characters with whatever the second character is.
    return match.groups()[0][1]

def remove_backslash_escapes(text):
    return _backslash_sub_re.sub(_replace_backslash_sub, text)


_backslash_add_re = re.compile(r'([\\"])')
def _add_backslash_sub(match):
    # Our regex matches single characters which need escaping,
    # so just return the character with a preceeding \
    return '\\' + match.groups()[0]

def add_backslash_escapes(text):
    return _backslash_add_re.sub(_add_backslash_sub, text)


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
