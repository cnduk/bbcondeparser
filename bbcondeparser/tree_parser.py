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

from collections import namedtuple

from . import _six as six

from bbcondeparser.token_parser import (
    get_tokens,
    TextToken,
    BadSyntaxToken,
    NewlineToken,
    OpenTagToken,
    CloseTagToken,
)

from bbcondeparser.tags import (
    ErrorText,
    RawText,
    NewlineText,
    parse_tag_set,
    RootTag,
)


class BaseTreeParser(object):
    tags = []
    ignored_tags = []

    raw_text_class = RawText
    error_text_class = ErrorText
    newline_text_class = NewlineText
    root_tag_class = RootTag

    def __init__(self, text):
        self._context = {}
        self.raw_text = text

        tags = parse_tag_set(self.tags)
        ignored_tags = set(
            tag.null_class
            for tag in parse_tag_set(self.ignored_tags)
            if tag not in tags
        )
        tags.update(ignored_tags)

        self.root_node = parse_tree(
            text, tags,
            raw_text_class=self.raw_text_class,
            error_text_class=self.error_text_class,
            newline_text_class=self.newline_text_class,
            root_tag_class=self.root_tag_class,
        )

        # Update the root node parent to self
        self.root_node.set_parent_node(self)

    def get_context(self):
        return self._context

    def render(self, ctx=None):
        if ctx:
            self._context = ctx
        return self.root_node.render()

    def pretty_format(self):
        return self.root_node.pretty_format()


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

    def pop(self):
        return self.stack.pop()

    def behead(self, index):
        """Reset the stack back to index and return the items
            removed from the top of the stack.
        e.g.
            stack = A, B, C, D, E, F, G
            index = 3
        results in:
            stack = A, B, C # stack[:index]
            returned = D, E, F, G # stack[index:]
        """
        self.stack[::], items = self.stack[:index], self.stack[index:]
        return items

    def push(self, *args, **kwargs):
        item = StackLevel(*args, **kwargs)
        self.stack.append(item)

    def open_for_index(self, token):
        assert isinstance(token, CloseTagToken)
        return self.find_last(
            lambda x: x.tag_cls.tag_name == token.tag_name
        )

    def first_newline_close_index(self):
        return self.find_first(
            lambda x: x.tag_cls.close_on_newline
        )

    def reset(self, index):
        """Clear the stack back to a certain point, and return the last
            item cleared form the stack
            e.g.
                stack = A, B, C, D, E, F, G
                index = 3
            results in:
                stack = A, B, C # stack[:index]
                returned = D (index #3)
                forgotten = E, F, G
        """
        return self.behead(index)[0]

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


def parse_tree(
    raw_text, tags, raw_text_class=RawText, error_text_class=ErrorText,
    newline_text_class=NewlineText, root_tag_class=RootTag,
):
    """`raw_text` is the raw bb code (conde format) to be parsed
        `tags` should be an iterable of tag classes allowed in the text
    """
    inst = _TreeParser(raw_text, tags, raw_text_class,
            error_text_class, newline_text_class, root_tag_class)
    inst.parse_tree()
    return inst.root_node

# This class is relatively straight forward, apart from what it does
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
#              v           # EOF
# [A][B][C][/A]            #
# S:                       # stack is empty. A was popped off and was given
# T: A(error(B), error(C)) # the tree from the last step
# This is done differently for newline closing, tag closing ([/tagname]),
# and encountering the end of the file.

class _TreeParser(object):
    def __init__(self, raw_text, tags, raw_text_class=RawText,
        error_text_class=ErrorText, newline_text_class=NewlineText,
        root_tag_class=RootTag,
    ):
        self.raw_text_class = raw_text_class
        self.error_text_class = error_text_class
        self.newline_text_class = newline_text_class
        self.root_tag_class = root_tag_class

        self.tokens = get_tokens(raw_text)
        self.tag_dict = create_tag_dict(tags)

        self._tree = None
        self.stack = TreeStack()
        self.root_node = None

        self.token_index = 0

    @property
    def tag_cls(self):
        return self.tag_dict.get(self.token.tag_name)

    def parse_tree(self):
        self._tree = []
        while self.token_index <= len(self.tokens):
            try:
                self.token = self.tokens[self.token_index]
            except IndexError:
                self.token = None

            if isinstance(self.token, TextToken):
                self.append_tree(self.raw_text_class(self.token.text))

            elif isinstance(self.token, BadSyntaxToken):
                self.append_err(self.token.reason)

            elif isinstance(self.token, OpenTagToken):
                self.handle_open_token()

            elif isinstance(self.token, CloseTagToken):
                self.handle_close_token()

            elif isinstance(self.token, NewlineToken):
                self.handle_newline_token()

            elif self.token is None:
                # This might cause us to backtrack, which is why it's
                # not just a call outside the while.
                self.handle_eof()

            else:
                raise TypeError("Unknown token type: {}".format(
                        type(self.token)))

            self.token_index += 1

        # Move tree from self to a root tag
        root_tag = self.root_tag_class({}, self._tree, '', '')
        self._tree = None
        self.root_node = root_tag

    def handle_open_token(self):
        if self.tag_cls is None:
            self.append_err('unknown tag')

        elif self.tag_cls.self_closing:
            # [] because self-closing tags contain no tree
            # "" beacuse self-closing tags don't have any end text
            inst = self.tag_cls(self.token.attrs, [], self.token.text, "")

            if inst.errors:
                self.append_err("; ".join(inst.errors))

            else:
                self.append_tree(inst)

        else:
            # Check if the attrs are ok first. if not, it's an error!
            _, errors = self.tag_cls.parse_attrs(self.token.attrs)
            if errors:
                self.append_err("; ".join(errors))
            # It's an open tag, so push onto the stack
            else:
                self.stack_push()

    def handle_close_token(self):
        open_for_index = self.stack.open_for_index(self.token)

        if open_for_index == -1:
            self.append_err("close tag does not match any open tag")

        else:
            # if the open for is not the last thing on the stack, then
            # we've short circuited the other things on the stack.
            # we'll need to start again from the first (now bad) tag.
            # (which sits at open_for_index +1)
            if open_for_index < len(self.stack) -1:
                self.stack_reset(open_for_index + 1, reset=True)
                self.append_err("open tag short-circuited by "
                        "differing close tag")

            else:
                tag_tree = self._tree
                close_token = self.token
                self.stack_pop()
                self.append_tree(self.tag_cls(
                    self.token.attrs, tag_tree,
                    self.token.text, close_token.text,
                ))

    def handle_newline_token(self):
        first_newline_close = self.stack.first_newline_close_index()

        if first_newline_close == -1:
            if self._tree and isinstance(self._tree[-1], self.newline_text_class):
                self._tree[-1].add_newline(self.token.text)
            else:
                self.append_tree(self.newline_text_class(self.token.text))

        else:
            first_non_newline_close = self.stack.find_first(
                lambda x: not x.tag_cls.close_on_newline,
                min=first_newline_close,
            )

            if first_non_newline_close != -1:
                # There's an item which doesn't want to be closed by a newline
                # after the first item which does want to be closed by a
                # newline. this newline has therefore short-circuited the tag
                # at this index. So we need to go back and re-evaluate the
                # tokens from that location.
                self.stack_reset(first_non_newline_close, reset=True)
                self.append_err("Open tag short-circuited by "
                        "newline closed outer tag")
            else:
                # everything from the first close_on_newline tag on the stack
                # to the last is a close_on_newline. So lets close them.
                closed_items = self.stack.behead(first_newline_close)

                close_token = self.token
                while closed_items:
                    tag_tree = self._tree
                    self.set_state(closed_items.pop())

                    self.append_tree(self.tag_cls(
                        self.token.attrs, tag_tree,
                        self.token.text, '',
                    ))

                # And now add our newline at the end.
                self.append_tree(self.newline_text_class(close_token.text))

    def handle_eof(self):
        if self.stack:
            # The first unclosed token has not been closed, so we have to
            # go back and start again.
            self.stack_reset(0, reset=True)
            self.append_err("missing close tag")

    def stack_push(self):
        self.stack.push(self._tree, self.tag_dict, self.tag_cls,
                self.token, self.token_index)
        self._tree = []
        self.tag_dict = get_new_tag_dict(self.tag_cls, self.tag_dict)

    def stack_reset(self, index, reset=False):
        self.set_state(self.stack.reset(index), reset)

    def stack_pop(self, reset=False):
        self.set_state(self.stack.pop(), reset)

    def set_state(self, stack_ctx, reset=False):
        self._tree = stack_ctx.tree
        self.tag_dict = stack_ctx.tag_dict
        self.token = stack_ctx.tag_open_token

        if reset:
            self.token_index = stack_ctx.token_index

    def append_err(self, reason):
        self.append_tree(self.error_text_class(self.token.text, reason))

    def append_tree(self, item):
        self._tree.append(item)


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
