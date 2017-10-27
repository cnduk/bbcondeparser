
# Copyright (c) 2017 Conde Nast Britain
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import cgi

from . import _six as six

from .tags import (
    RawText, BaseTagMeta, BaseTag, NewlineText, ErrorText, RootTag)
from .tree_parser import BaseTreeParser


HTML_NEWLINE = '<br />'
NEWLINE_BEHAVIOURS = {
    None: 0,
    'convert': 1,
    'ignore': 2,
    'remove': 3,
}
RENDERABLE_TEXT = (ErrorText, RawText)


def is_inline_tag(tag):
    """Check if the tag is inline.

    Args:
        tag (BaseHTMLTag): the tag to check

    Returns:
        bool: is it inline?
    """
    return getattr(tag, 'tag_display', None) == 'inline'


def is_block_tag(tag):
    """Check if the tag is block.

    Args:
        tag (BaseHTMLTag): the tag to check

    Returns:
        bool: is it block?
    """
    return getattr(tag, 'tag_display', None) == 'block'


def escape_html(text):
    """Escape html text.

    Args:
        text (str): text to escape

    Returns:
        str: the escaped text
    """
    return cgi.escape(text, quote=True)


class HTMLNewlineText(NewlineText):
    """HTML version of NewlineText."""

    def _render(self):
        return '<br />' * self.count


class HTMLText(RawText):
    """HTML version of RawText."""

    def render(self):
        """Render the text.

        Args:
            **kwargs: things

        Returns:
            str: escaped html text
        """
        text = super(HTMLText, self).render()
        return escape_html(text)

    def render_raw(self):
        """Render the text un-html-escaped.

        Returns:
            str: the raw text
        """
        return self.render()


class BaseHTMLTagMeta(BaseTagMeta):
    """Metaclass oh boy oh boy."""

    @staticmethod
    def validate_tag_cls(tag_cls):
        """Validate the class being created.

        Args:
            tag_cls (BaseHTMLTag): tag class

        Raises:
            RuntimeError: if some values are set and shouldnt
        """

        if tag_cls.newline_behaviour not in NEWLINE_BEHAVIOURS:
            raise RuntimeError('newline_behaviour must be one of {}'.format(
                NEWLINE_BEHAVIOURS))

        if is_inline_tag(tag_cls) and tag_cls.convert_paragraphs:
            raise RuntimeError(
                "Cannot enable convert_paragraphs "
                "on inline tag {tag_cls.tag_name}".format(tag_cls=tag_cls))

        if not is_inline_tag(tag_cls) and not is_block_tag(tag_cls):
            raise RuntimeError(
                "Unknown tag display type: {tag_cls.tag_type}"
                "on {tag_cls.tag_name}".format(tag_cls=tag_cls))


def apply_ctx(new_ctx, src_ctx):

    for ctx_key, ctx_value in src_ctx.iteritems():
        if ctx_key in new_ctx:
            current_value = new_ctx[ctx_key]

            if ctx_key in ('convert_paragraphs', 'trim_whitespace'):
                if current_value is None:
                    new_ctx[ctx_key] = ctx_value
                elif ctx_value is False:
                    new_ctx[ctx_key] = False

            elif ctx_key == 'newline_behaviour':
                if NEWLINE_BEHAVIOURS[ctx_value] > NEWLINE_BEHAVIOURS[current_value]:
                    new_ctx[ctx_key] = ctx_value

            else:
                new_ctx[ctx_key] = ctx_value

        else:
            new_ctx[ctx_key] = ctx_value

    return new_ctx


@six.add_metaclass(BaseHTMLTagMeta)
class BaseHTMLTag(BaseTag):
    """BaseHTMLTag, used for all HTML tags.

    Attributes:
        convert_newlines (bool, str): convert newlines to the HTML equivalent,
            can be True, False or 'inherit'
        convert_paragraphs (bool, str): convert double newlines to paragraphs,
            can be True, False or 'inherit'
        tag_display (str): tag display mode - block or inline
    """

    tag_display = 'inline'
    newline_behaviour = None
    convert_paragraphs = None
    trim_whitespace = None

    def find_children_instances(self, cls, multi=True):
        """This method searches immediate children for instances of `cls`
            if `multi` is truthy, then a list of found instances is returned.
            if `multi` is falsy, then only the last found instance is
                returned, and any extra instances found before hand are
                replaced with ErrorText.
                If no instance is found, `None` is returned.
        """
        if len(self.tree) == 0:
            return None

        items = [
            (index, child)
            for index, child in enumerate(self.tree)
            if isinstance(child, cls)
        ]

        if multi:
            return [child for _, child in items]

        if len(items) == 0:
            return None

        if len(items) > 1:
            # Too many, use `index` from `items` to find bad children,
            # and replace with ErrorText
            for index, child in items[:-1]:
                self.tree[index] = ErrorText(
                    child.render_raw(),
                    reason="Extra {} tag".format(child.tag_name)
                )

        # Return the last defined
        return items[-1][1]

    def render(self):
        """Return the rendering of this tag (including children)
            (N.B. This inherintly includes children, no way not to.
        """
        child_text = self._render()

        if self.trim_whitespace:
            child_text = child_text.strip()

        return child_text


class RootHTMLTag(RootTag):
    newline_behaviour = None
    convert_paragraphs = None
    trim_whitespace = None


class HtmlSimpleTag(BaseHTMLTag):
    """HTML version of SimpleTag.

    Attributes:
        replace_text (str): text to replace in template
        template (str): basic template
    """

    template = None
    replace_text = '{{ body }}'
    convert_paragraphs = False

    def _render(self):
        rendered_children = self.render_children()

        if self.template is None:
            return rendered_children

        else:
            return self.template.replace(self.replace_text, rendered_children)


class ParagraphTag(BaseHTMLTag):
    tag_name = 'p'
    # It is block but has the behaviour of an inline
    tag_display = 'inline'
    convert_paragraphs = False

    def _render(self):
        return '<p>{children}</p>'.format(children=self.render_children())


class BaseHTMLRenderTreeParser(BaseTreeParser):
    """I've been intensely thinking about how the paragraphs and newline
    conversions should work and this is how:

    The parent of the node, whether that be another node or the parser
    passes down if the values should be converted but only if its False.
    For instance, if the parser is False for newlines and paragraphs,
    nowhere should there be converted newlines or paragraphs.

    However if we think of this:
        parser {convert_newlines=True}
            text
            infobox {convert_newlines=False}
                text
                text
                infobox2 {convert_newlines=True}
                    text
                    text
                text
            text

        should produce

        parser {convert_newlines=True}
            text
            <br />
            infobox {convert_newlines=False}
                text
                text
                infobox2 {convert_newlines=True}
                    text
                    text
                text
            <br />
            text

    Attributes:
        convert_newlines (bool): allow newline conversion
        convert_paragraphs (bool): allow paragraph conversion
        newline_text_class (NewlineText): type of class to use for newlines
        raw_text_class (RawText): type of class to use for raw text
        strip_newlines (bool): remove newlines

    """

    raw_text_class = HTMLText
    newline_text_class = HTMLNewlineText
    root_tag_class = RootHTMLTag
    newline_behaviour = None
    convert_paragraphs = None

    def __init__(self, text, newline_behaviour=None, convert_paragraphs=None):
        super(BaseHTMLRenderTreeParser, self).__init__(text)

        self.root_node.newline_behaviour = newline_behaviour or self.newline_behaviour
        self.root_node.convert_paragraphs = convert_paragraphs or self.convert_paragraphs
        self._parse_tree()

    def _parse_tree(self):

        scope_stack = [{}]

        def push_scope(node):
            new_scope = apply_ctx(get_scope().copy(), {
                'convert_paragraphs': node.convert_paragraphs,
                'newline_behaviour': node.newline_behaviour,
            })
            scope_stack.append(new_scope)

        def pop_scope():
            scope_stack.pop()

        def get_scope():
            return scope_stack[-1]

        def _parse_node(parsed_node):

            push_scope(parsed_node)

            scope = get_scope()
            convert_paragraphs = scope['convert_paragraphs'] is True
            remove_newlines = scope['newline_behaviour'] == 'remove'
            convert_newlines = scope['newline_behaviour'] == 'convert'

            new_tree = []
            paragraph_scope = None
            inside_paragraph = False

            for node_index, node in enumerate(parsed_node.tree):

                if is_inline_tag(node):

                    node.tree = _parse_node(node)

                    if convert_paragraphs:
                        if not inside_paragraph:
                            inside_paragraph = True
                            paragraph_scope = [node]
                        else:
                            paragraph_scope.append(node)
                    else:
                        new_tree.append(node)

                elif is_block_tag(node):

                    if inside_paragraph and paragraph_scope:
                        # clone paragraph scope?
                        paragraph_node = ParagraphTag(
                            {}, paragraph_scope, '', '')
                        new_tree.append(paragraph_node)
                        paragraph_scope = None
                        inside_paragraph = False

                    node.tree = _parse_node(node)
                    new_tree.append(node)

                elif isinstance(node, RENDERABLE_TEXT):

                    if convert_paragraphs:
                        if not inside_paragraph:
                            inside_paragraph = True
                            paragraph_scope = [node]
                        else:
                            paragraph_scope.append(node)

                    else:
                        new_tree.append(node)

                elif isinstance(node, NewlineText):

                    # Open/close a paragraph
                    if node.count >= 2 and convert_paragraphs:

                        # Close paragraph, wrap in tag, add as node
                        if inside_paragraph and paragraph_scope:
                            # clone paragraph scope?
                            paragraph_node = ParagraphTag(
                                {}, paragraph_scope, '', '')
                            new_tree.append(paragraph_node)
                            paragraph_scope = None
                            inside_paragraph = False

                        # Open paragraph and scope. Dont need to add node.
                        else:
                            inside_paragraph = True
                            paragraph_scope = []

                    else:
                        if convert_newlines:
                            # we dont want to put <br/> in between blocks so
                            # we actually only want to put them in paragraphs
                            # if we're converting or anywhere if we're not
                            # converting paragraphs
                            if inside_paragraph:
                                paragraph_scope.append(node)
                            elif not convert_paragraphs:
                                new_tree.append(node)
                            else:
                                # Not removing and not converting so change
                                # back to NewlineText
                                new_node = NewlineText(node.text)
                                new_node.count = node.count
                                new_tree.append(new_node)

                        elif not remove_newlines:
                            # Not removing and not converting so change back
                            # to NewlineText
                            new_node = NewlineText(node.text)
                            new_node.count = node.count
                            if inside_paragraph:
                                paragraph_scope.append(new_node)
                            else:
                                new_tree.append(new_node)

            if inside_paragraph and paragraph_scope:
                paragraph_node = ParagraphTag({}, paragraph_scope, '', '')
                new_tree.append(paragraph_node)
                paragraph_scope = None
                inside_paragraph = False

            pop_scope()
            return new_tree

        self.root_node.tree = _parse_node(self.root_node)
