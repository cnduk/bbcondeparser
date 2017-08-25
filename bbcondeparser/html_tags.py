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

import cgi

from . import _six as six

from .utils import strip_newlines
from .tags import RawText, BaseTagMeta, BaseTag, NewlineText
from .tree_parser import BaseTreeParser


HTML_NEWLINE = '<br />'


def is_inline_tag(tag):
    return getattr(tag, 'tag_display', None) == 'inline'


def is_block_tag(tag):
    return getattr(tag, 'tag_display', None) == 'block'


def escape_html(text):
    return cgi.escape(text, quote=True)


class HTMLNewlineText(NewlineText):
    def _render(self):
        return '<br />' * self.count


class HTMLText(RawText):
    def render(self, **kwargs):
        text = self._render()
        return escape_html(text)

    def render_raw(self):
        # Want to escape html
        return self.render()


class BaseHTMLTagMeta(BaseTagMeta):
    @staticmethod
    def validate_tag_cls(tag_cls):
        BaseTagMeta.validate_tag_cls(tag_cls)

        if tag_cls.strip_newlines and tag_cls.convert_newlines:
            raise RuntimeError(
                "Cannot enable strip_newlines and convert_newlines"
                " on {tag_cls.tag_name}".format(tag_cls=tag_cls))

        if is_inline_tag(tag_cls) and tag_cls.convert_paragraphs:
            raise RuntimeError(
                "Cannot enable convert_paragraphs "
                "on inline tag {tag_cls.tag_name}".format(tag_cls=tag_cls))


@six.add_metaclass(BaseHTMLTagMeta)
class BaseHTMLTag(BaseTag):
    tag_display = 'inline'
    convert_newlines = False  # converts newlines to HTML_NEWLINE
    convert_paragraphs = False

    def render_children(self, convert_paragraphs=None):

        # TODO: tidy this
        if convert_paragraphs is None:
            convert_paragraphs = self.convert_paragraphs
        elif convert_paragraphs is False and self.convert_paragraphs is True:
            convert_paragraphs = False
        else:
            convert_paragraphs = self.convert_paragraphs

        if is_block_tag(self):
            child_text = render_tree(
                self.tree, self.convert_newlines, convert_paragraphs)
        else:
            child_text = render_tree(
                self.tree, self.convert_newlines, False)

        if self.strip_newlines:
            child_text = strip_newlines(child_text)

        if self.trim_whitespace:
            child_text = child_text.strip()

        return child_text


class HtmlSimpleTag(BaseHTMLTag):
    template = None
    replace_text = '{{ body }}'

    def _render(self):
        if self.template is None:
            return self.render_children()

        return self.template.replace(
            self.replace_text, self.render_children()
        )


class BaseHTMLRenderTreeParser(BaseTreeParser):
    raw_text_class = HTMLText
    newline_text_class = HTMLNewlineText
    convert_newlines = False
    convert_paragraphs = False

    def render(self):
        child_text = render_tree(
            self.tree, self.convert_newlines, self.convert_paragraphs)

        return child_text


def peek_node(tree, node_index):
    try:
        return tree[node_index]
    except IndexError:
        return False


def render_tree(tree, convert_newlines=False, convert_paragraphs=False):
    """Walks through the nodes in the tree trying to work out where the
       correct location is to insert paragraph tags
    """

    # TODO: include newline removing

    rendered_children = []
    inside_paragraph = False

    for node_index, node in enumerate(tree):

        if is_inline_tag(node):
            if convert_paragraphs and not inside_paragraph:
                rendered_children.append('<p>')
                inside_paragraph = True
            rendered_children.append(node.render())

        elif is_block_tag(node):
            if convert_paragraphs and inside_paragraph:
                rendered_children.append('</p>')
                inside_paragraph = False
            rendered_children.extend(node.render())

        elif isinstance(node, HTMLText):
            if convert_paragraphs and not inside_paragraph:
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

                else:
                    rendered_children.append(node.render_raw())

            else:
                if convert_newlines:
                    rendered_children.append(node.render())
                else:
                    rendered_children.append(node.render_raw())

    if convert_paragraphs and inside_paragraph:
        rendered_children.append('</p>')
        inside_paragraph = False

    return ''.join(rendered_children)
