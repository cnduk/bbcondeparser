
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
        ctx_default = tag_cls.context_default
        ctx_override = tag_cls.context_override

        newline_behaviour = ctx_default.get('newline_behaviour')
        if newline_behaviour not in NEWLINE_BEHAVIOURS:
            raise RuntimeError('newline_behaviour must be one of {}'.format(
                NEWLINE_BEHAVIOURS))

        newline_behaviour = ctx_override.get('newline_behaviour')
        if newline_behaviour not in NEWLINE_BEHAVIOURS:
            raise RuntimeError('newline_behaviour must be one of {}'.format(
                NEWLINE_BEHAVIOURS))

        if is_inline_tag(tag_cls)\
            and (
                ctx_default.get('convert_paragraphs') is True
                or ctx_override.get('convert_paragraphs') is True
        ):
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
    context_default = {
        'newline_behaviour': None,
        'convert_paragraphs': None,
        'trim_whitespace': None,
    }
    context_override = {}

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

    def get_context(self):
        if self._context is None:
            # Defaults
            new_ctx = self.context_default.copy()
            # Inherit
            if self._parent_node:
                inherited_ctx = self._parent_node.get_context().copy()
                new_ctx = apply_ctx(new_ctx, inherited_ctx)
            # Override
            new_ctx = apply_ctx(new_ctx, self.context_override)

            # Anything that is not a block tag must not render paragraphs
            if is_inline_tag(self):
                new_ctx['convert_paragraphs'] = False

            self._context = new_ctx

        return self._context

    def render(self):
        """Return the rendering of this tag (including children)
            (N.B. This inherintly includes children, no way not to.
        """
        child_text = self._render()

        if self.get_context().get('trim_whitespace', False):
            child_text = child_text.strip()

        return child_text

    def render_children(self):
        return render_tree(self)


class RootHTMLTag(RootTag):
    context_default = {
        'convert_paragraphs': None,
        'newline_behaviour': None,
        'trim_whitespace': None,
    }

    def get_context(self, ctx=None):
        if self._context is None or ctx:
            new_ctx = super(RootHTMLTag, self).get_context()
            if ctx:
                new_ctx.update(ctx)
            self._context = new_ctx

        return self._context

    def render(self, ctx=None):
        """Render the tag.

        Returns:
            str: the rendered tag
        """
        self.get_context(ctx=ctx)
        return render_tree(self)


class HtmlSimpleTag(BaseHTMLTag):
    """HTML version of SimpleTag.

    Attributes:
        replace_text (str): text to replace in template
        template (str): basic template
    """

    convert_newlines = False
    convert_paragraphs = False
    template = None
    replace_text = '{{ body }}'

    def _render(self):
        rendered_children = self.render_children()

        if self.template is None:
            return rendered_children

        else:
            return self.template.replace(self.replace_text, rendered_children)


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


def peek_node(tree, node_index):
    """Have a cheeky look at the next node in the tree.

    Args:
        tree (list): list of nodes
        node_index (int): node index to look at

    Returns:
        Tag, False: found tag or False if nothing is found
    """
    try:
        return tree[node_index]
    except IndexError:
        return False


def is_open_paragraph(node, convert_paragraphs, inside_paragraph):
    return node\
        and (is_inline_tag(node) or isinstance(node, RENDERABLE_TEXT))\
        and convert_paragraphs\
        and not inside_paragraph


def render_tree(parent_node):
    """Render the tree of tags.

    Args:
        tree (list): list of tags
        convert_newlines (bool, optional): whether to convert newlines
        convert_paragraphs (bool, optional): whether to convert paragraphs
        strip_newlines (bool, optional): whether to strip newlines

    Returns:
        str: rendered children
    """
    rendered_children = []
    inside_paragraph = False

    tree = parent_node.tree
    parent_ctx = parent_node.get_context()
    convert_paragraphs = parent_ctx.get('convert_paragraphs', False)
    convert_newlines = parent_ctx.get('newline_behaviour') == 'convert'
    strip_newlines = parent_ctx.get('newline_behaviour') == 'remove'

    for node_index, node in enumerate(tree):

        if is_inline_tag(node):
            if is_open_paragraph(node, convert_paragraphs, inside_paragraph):
                rendered_children.append('<p>')
                inside_paragraph = True
            rendered_children.append(node.render())

        elif is_block_tag(node):

            if is_inline_tag(parent_node):
                rendered_children.append(node.render_raw())

            else:
                if convert_paragraphs and inside_paragraph:
                    rendered_children.append('</p>')
                    inside_paragraph = False
                rendered_children.append(node.render())

        elif isinstance(node, RENDERABLE_TEXT):
            if is_open_paragraph(node, convert_paragraphs, inside_paragraph):
                rendered_children.append('<p>')
                inside_paragraph = True
            rendered_children.append(node.render())

        elif isinstance(node, NewlineText):
            if node.count > 1:
                if convert_paragraphs:
                    if inside_paragraph:
                        rendered_children.append('</p>')
                        inside_paragraph = False

                    next_node = peek_node(tree, node_index + 1)
                    if next_node and not is_block_tag(next_node):
                        rendered_children.append('<p>')
                        inside_paragraph = True

                    elif not strip_newlines:
                        rendered_children.append(node.render_raw())

                elif convert_newlines:
                    rendered_children.append(node.render())

                elif not strip_newlines:
                    rendered_children.append(node.render_raw())

            else:
                next_node = peek_node(tree, node_index + 1)
                if convert_newlines:
                    if not is_open_paragraph(
                            next_node, convert_paragraphs, inside_paragraph):
                        rendered_children.append(node.render())

                    elif not strip_newlines:
                        rendered_children.append(node.render_raw())

                elif not strip_newlines:
                    rendered_children.append(node.render_raw())

    if convert_paragraphs and inside_paragraph:
        rendered_children.append('</p>')
        inside_paragraph = False

    return ''.join(rendered_children)
