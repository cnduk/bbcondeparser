from collections import namedtuple

from bbcondeparser.token_parser import (
    get_tokens,
    TextToken,
    BadSyntaxToken,
    NewlineToken,
    OpenTagToken,
    CloseTagToken,
)

from bbcondeparser.tags import ErrorText, RawText, NewlineText, parse_tag_set

TAG_START = 'tag_start'
TAG_END = 'tag_end'


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
    ['tree', 'tag_dict', 'tag_cls', 'tag_open_token']
)
class TreeStack(object):
    def __init__(self):
        self.stack = []

    def __bool__(self):
        return len(self.stack) > 0

    __nonzero__ = __bool__ # python 2.x portability

    def pop(self):
        return self.stack.pop()

    def push(self, tree, tag_dict, tag_cls, tag_open_token):
        item = StackLevel(tree, tag_dict, tag_cls, tag_open_token)
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

    for token in tokens:
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
                stack.push(tree, tag_dict, tag_cls, token)
                tree = []
                tag_dict = get_new_tag_dict(tag_cls, tag_dict)

        # It's a close. First let's find if it's actually closing anything.
        elif isinstance(token, CloseTagToken):
            if not stack.contains_open_for(token):
                tree.append(error_text_class(
                    token.text, "Close tag does not match any open tag"
                ))

            else:
                while stack:
                    tag_tree = tree
                    tree, tag_dict, tag_cls, open_token = stack.pop()

                    if not tag_cls.tag_name == token.tag_name:
                        tree.append(error_text_class(
                            open_token.text,
                            "Open tag short-circuited by close tag"
                        ))
                        tree.extend(tag_tree)

                    else:
                        tree.append(tag_cls(open_token.attrs, tag_tree,
                                open_token.text, token.text))

                        break


        elif isinstance(token, NewlineToken):
            if not stack.want_close_on_newline():
                if tree and isinstance(tree[-1], newline_text_class):
                    tree[-1].add_newline(token.text)
                else:
                    tree.append(newline_text_class(token.text))

            else:
                while stack:
                    tag_tree = tree
                    tree, tag_dict, tag_cls, open_token = stack.pop()

                    if not tag_cls.close_on_newline:
                        tree.append(error_text_class(
                            open_token.text,
                            "Open tag short-circuited by newline closed outer tag"
                        ))
                        tree.extend(tag_tree)

                    elif stack.want_close_on_newline():
                        tree.append(tag_cls(open_token.attrs, tag_tree,
                                open_token.text, ''))

                    else:
                        tree.append(tag_cls(open_token.attrs, tag_tree,
                                open_token.text, token.text))
                        break

    while stack:
        tag_tree = tree
        tree, tag_dict, tag_cls, open_token = stack.pop()

        tree.append(error_text_class(open_token.text, "Missing close tag"))
        tree.extend(tag_tree)

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
