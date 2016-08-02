from collections import namedtuple
from operator import attrgetter

import six

from bbcondeparser.token_parser import (
    get_tokens,
    TextToken,
    BadSyntaxToken,
    NewlineToken,
    OpenTagToken,
    CloseTagToken,
)

from bbcondeparser.tags import ErrorText, RawText, NewlineText, parse_tag_set

class BaseTreeParser(object):
    tags = []
    ignored_tags = []

    raw_text_class = RawText
    error_text_class = ErrorText
    newline_text_class = NewlineText

    def __init__(self, text):
        self.raw_text = text

        ignored_tags = [tag.null_class for tag in self.ignored_tags]
        tags = self.tags + ignored_tags

        self.tree = parse_tree(
            text, tags,
            raw_text_class=self.raw_text_class,
            error_text_class=self.error_text_class,
            newline_text_class=self.newline_text_class,
        )

    def render(self):
        return ''.join(tag.render() for tag in self.tree)

    def pretty_format(self):
        return '\n'.join(
            getattr(child, 'pretty_format', child.__repr__)()
            for child in self.tree
        )


StackLevel = namedtuple(
    'TreeParserStackLevel',
    ['tree', 'tag_dict', 'tag_cls', 'tag_open_token', 'token_index']
)
class TreeStack(object):
    def __init__(self):
        self.stack = []

    def __bool__(self):
        return len(self) > 0

    __nonzero__ = __bool__ # python 2.x portability

    def __len__(self):
        return len(self.stack)

    def __getitem__(self, index):
        return self.stack(index)

    @property
    def head(self):
        return self.stack[-1]

    def pop(self):
        return self.stack.pop()

    def push(self, *args, **kwargs):
        item = StackLevel(*args, **kwargs)
        self.stack.append(item)

    def contains_open_for(self, token):
        assert isinstance(token, CloseTagToken)
        return any(
            stack_level.tag_cls.tag_name == token.tag_name
            for stack_level in self.stack
        )

    def want_close_on_newline(self):
        return any(
            stack_level.tag_cls.close_on_newline
            for stack_level in self.stack
        )

    def reset(self, index):
        """Clear the stack back to a certain point, and return the last
            item cleared form the stack
            e.g.
            stack = A, B, C, D, E, F, G
            index = 3
            results in:
            stack = A, B, C
            returned = D (index #3)
            forgotten = E, F, G
        """
        item = self.stack[index]
        self.stack = self.stack[:index]
        return item

    def find_first(self, filter, min=0):
        """return the lowest item in the stack meets `filter`,
            or -1 if not found
            `filter` - a callable which takes a stack item, and returns
                a truthy object if this item should be returned, a falsy
                object otherwise.
            `min` - the index from which to search

            e.g. stack = A, B, B, C
            filter = lambda x: x == B
            returns 1

            e.g. stack = A, B, B, C
            filter = lambda x: x == B
            min = 2
            returns 2
        """
        assert six.callable(filter)

        for index, item in enumerate(self.stack[min:], min):
            if filter(item):
                return index
        return -1

    def find_last(self, filter):
        """return the highest item in the stack meets `filter`,
            or -1 if not found
            `filter` - a callable which takes a stack item, and returns
                a truthy object if this item should be returned, a falsy
                object otherwise.
            `max` - the index from which to search down

            e.g. stack = A, B, B, C
            filter = lambda x: x == B
            returns 2
        """
        assert six.callable(filter)

        indexes = range(len(self.stack)-1, -1, -1)
        items = self.stack[::-1]

        for index, item in zip(indexes, items):
            if filter(item):
                return index
        return -1


# This function is relatively straight forward, apart from what it does
# when it encounters an error and has to re-evaluate tokens it's already
# parsed. consider the following setup
#  A(B)  - tag A accepts only B tags
#  B(C)  - tag B accepts only C tags
#  C(<self closing>) - tag C is self closing.
#  input = '[A][B][C][/A]'
# As we're processing the input, we'll get to the point where our
# working looks like this:
#          v    # currently pointing at token [/A]
# [A][B][C][/A] #
# S: A, B       # stack holds tag A and B
# T: C          # parsed C happily under the context of B
#
# At this point, we need to go back and add the B as being in error,
# But we can't just then re-add C as it's not valid under A, so we need
# to re-process C
#       v       # now pointing at token [C]
# [A][B][C][/A] #
# S: A          # stack holds tag A
# T: error(B)   # tree holds error container for B's text
#          v            # now pointing at token [/A]
# [A][B][C][/A]         #
# S: A                  # stack still holds A
# T: error(B), error(C) # C was no longer valid under A, so its error container
#                       # has been added to the tree
#              v           # not pointing at the EOF
# [A][B][C][/A]            #
# S:                       # stack is empty. A was popped off and was given
# T: A(error(B), error(C)) # the tree from the last step
# This is done differently for newline closing, tag closing ([/tagname]),
# and encountering the end of the file.
def parse_tree(
    raw_text, tags, raw_text_class=RawText, error_text_class=ErrorText,
    newline_text_class=NewlineText,
):
    """`raw_text` is the raw bb code (conde format) to be parsed
        `tags` should be an iterable of tag classes allowed in the text
    """
    tokens = get_tokens(raw_text)
    tag_dict = create_tag_dict(tags)

    stack = TreeStack()
    tree = []

    token_index = 0
    while token_index <= len(tokens):
        try:
            token = tokens[token_index]
        except IndexError:
            token = None

        if isinstance(token, TextToken):
            tree.append(raw_text_class(token.text))

        elif isinstance(token, BadSyntaxToken):
            tree.append(error_text_class(token.text, token.reason))

        elif isinstance(token, OpenTagToken):
            tag_cls = tag_dict.get(token.tag_name)

            if tag_cls is None:
                tree.append(error_text_class(token.text, "unknown tag"))

            elif tag_cls.self_closing:
                # "[]" because self-closing tags contain no tree.
                tree.append(tag_cls(token.attrs, [], token.text, ""))

            else:
                # It's an open tag, so push onto the stack
                stack.push(tree, tag_dict, tag_cls, token, token_index)
                tree = []
                tag_dict = get_new_tag_dict(tag_cls, tag_dict)

        elif isinstance(token, CloseTagToken):
            open_for_index = stack.find_last(
                lambda x: x.tag_cls.tag_name == token.tag_name
            )

            if open_for_index == -1:
                tree.append(error_text_class(
                    token.text, "Close tag does not match any open tag"
                ))

            else:
                # if the open for is not the last thing on the stack, then
                # we've short circuited the other things on the stack.
                # we'll need to start again from the first (now bad) tag.
                # (which sits at open_for_index + 1)
                if open_for_index < len(stack) -1:
                    tree, tag_dict, tag_cls, open_token, token_index = \
                            stack.reset(open_for_index + 1)
                    tree.append(error_text_class(
                        open_token.text,
                        "Open tag short-circuited by differing close tag",
                    ))

                else:
                    tag_tree = tree
                    tree, tag_dict, tag_cls, open_token, old_token_index = \
                            stack.pop()

                    tree.append(tag_cls(open_token.attrs, tag_tree,
                            open_token.text, token.text))

        elif isinstance(token, NewlineToken):
            if not stack.want_close_on_newline():
                if tree and isinstance(tree[-1], newline_text_class):
                    tree[-1].add_newline(token.text)
                else:
                    tree.append(newline_text_class(token.text))

            else:
                first_newline_close = stack.find_first(
                    lambda x: x.tag_cls.close_on_newline
                )

                first_non_newline_close = stack.find_first(
                    lambda x: not x.tag_cls.close_on_newline,
                    min=first_newline_close,
                )

                if first_non_newline_close != -1:
                    # Theres an item which doesn't want to be closed by a
                    # newline after the first item which does want to be
                    # closed by a newline. this newline has therefore
                    # short-circuited the tag at this index. So we need
                    # to go back and re-evaluate the tokens from that
                    # location.
                    tree, tag_dict, tag_cls, open_token, token_index = \
                            stack.reset(first_non_newline_close)
                    tree.append(error_text_class(
                        open_token.text,
                        "Open tag short-circuited by newline closed outer tag",
                    ))

                else:
                    # Everything from the first "want close on newline" to
                    # the last want to close on newline, so lets close them.
                    while stack.want_close_on_newline():
                        tag_tree = tree
                        tree, tag_dict, tag_cls, open_token, old_token_index = stack.pop()

                        if stack.want_close_on_newline():
                            end_text = ''
                        else:
                            end_text = token.text

                        tree.append(tag_cls(open_token.attrs, tag_tree,
                                open_token.text, end_text))

        elif token is None and stack:
            # The first unclosed token has not been closed, so we have to
            # go back and start again.
            tree, tag_dict, tag_cls, open_token, token_index = stack.reset(0)
            tree.append(error_text_class(open_token.text, "Missing close tag"))

        token_index += 1

    return tree

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
