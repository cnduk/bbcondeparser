
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

from .tags import RawText, BaseTagMeta, BaseTag, NewlineText, ErrorText
from .tree_parser import BaseTreeParser


HTML_NEWLINE = '<br />'
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

    def render(self, **kwargs):
        """Render the text.

        Args:
            **kwargs: things

        Returns:
            str: escaped html text
        """
        text = self._render()
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
        BaseTagMeta.validate_tag_cls(tag_cls)

        if tag_cls.strip_newlines is True and tag_cls.convert_newlines:
            raise RuntimeError(
                "Cannot enable strip_newlines and convert_newlines"
                " on {tag_cls.tag_name}".format(tag_cls=tag_cls))

        if is_inline_tag(tag_cls) and tag_cls.convert_paragraphs is True:
            raise RuntimeError(
                "Cannot enable convert_paragraphs "
                "on inline tag {tag_cls.tag_name}".format(tag_cls=tag_cls))

        if not is_inline_tag(tag_cls) and not is_block_tag(tag_cls):
            raise RuntimeError(
                "Unknown tag display type: {tag_cls.tag_type}"
                "on {tag_cls.tag_name}".format(tag_cls=tag_cls))


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
    convert_newlines = 'inherit'
    convert_paragraphs = 'inherit'
    strip_newlines = 'inherit'

    def render(self, convert_newlines=False, convert_paragraphs=False,
               strip_newlines=False):
        """Return the rendering of this tag (including children)
            (N.B. This inherintly includes children, no way not to.
        """
        text = self._render(
            convert_newlines=convert_newlines,
            convert_paragraphs=convert_paragraphs,
            strip_newlines=strip_newlines,
        )

        if self.trim_whitespace:
            text = text.strip()

        return text

    def render_children(self, convert_newlines=False, convert_paragraphs=False,
                        strip_newlines=False):
        """Render the children of the tag.

        Args:
            convert_newlines (None, optional): convert newline overwrite
            convert_paragraphs (None, optional): convert paragraph overwrite
            strip_newlines (None, optional): strip newline overwrite

        Returns:
            str: rendered children
        """

        if self.convert_newlines != 'inherit':
            convert_newlines = self.convert_newlines

        if self.convert_paragraphs != 'inherit':
            convert_paragraphs = self.convert_paragraphs

        if self.strip_newlines != 'inherit':
            strip_newlines = self.strip_newlines

        if is_block_tag(self):
            child_text = render_tree(
                self, convert_newlines, convert_paragraphs, strip_newlines)
        else:
            # Inline tags never render paragraphs
            child_text = render_tree(
                self, convert_newlines, False, strip_newlines)

        if self.trim_whitespace:
            child_text = child_text.strip()

        return child_text


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

    def _render(self, convert_newlines=False, convert_paragraphs=False,
                strip_newlines=False):

        rendered_children = self.render_children(
            convert_newlines=convert_newlines,
            convert_paragraphs=convert_paragraphs,
            strip_newlines=strip_newlines,
        )

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
    convert_newlines = False
    convert_paragraphs = False
    strip_newlines = False

    def render(self):
        """Render the tag.

        Returns:
            str: the rendered tag
        """
        child_text = render_tree(
            self, self.convert_newlines, self.convert_paragraphs,
            self.strip_newlines,
        )

        return child_text


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


def render_tree(parent_node, convert_newlines=False, convert_paragraphs=False,
                strip_newlines=False):
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

    for node_index, node in enumerate(tree):

        if is_inline_tag(node):
            if is_open_paragraph(node, convert_paragraphs, inside_paragraph):
                rendered_children.append('<p>')
                inside_paragraph = True
            rendered_children.append(node.render(
                convert_newlines=convert_newlines,
                convert_paragraphs=convert_paragraphs,
                strip_newlines=strip_newlines,
            ))

        elif is_block_tag(node):

            if is_inline_tag(parent_node):
                rendered_children.append(node.render_raw())

            else:
                if convert_paragraphs and inside_paragraph:
                    rendered_children.append('</p>')
                    inside_paragraph = False
                rendered_children.extend(node.render(
                    convert_newlines=convert_newlines,
                    convert_paragraphs=convert_paragraphs,
                    strip_newlines=strip_newlines,
                ))

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
