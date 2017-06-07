import cgi

import six

from .utils import strip_newlines
from .tags import RawText, BaseTagMeta, BaseTag, NewlineText
from .tree_parser import BaseTreeParser


HTML_NEWLINE = '<br />'


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



@six.add_metaclass(BaseHTMLTagMeta)
class BaseHTMLTag(BaseTag):
    convert_newlines = False # converts newlines to HTML_NEWLINE
    convert_paragraphs = False

    def render_children(self):
        if self.convert_paragraphs:
            child_text = render_paragraphs(self.tree)
        else:
            child_text = ''.join(child.render() for child in self.tree)

        # These convert and strip are mutually exclusive,
        # enfored by the metaclass
        if self.convert_newlines:
            child_text = convert_newlines(child_text)

        if self.strip_newlines:
            child_text = strip_newlines(child_text)

        if self.trim_whitespace:
            child_text = child_text.strip()

        return child_text

    def render(self):
        text = super(BaseHTMLTag, self).render()

        if self.convert_newlines:
            text = convert_newlines(text)

        return text


class BaseHTMLRenderTreeParser(BaseTreeParser):
    raw_text_class = HTMLText



def escape_html(text):
    return cgi.escape(text, quote=True)


def convert_newlines_to_html(text, newline_char='\n', convert_char='<br />'):
    """Converts the new line character into the convert character
    """

    return text.replace(newline_char, convert_char)

def get_paragraph_insert_index(tree):
    """Walks through the tree trying to find a place to insert a paragraph
    """

    length = len(tree) - 1
    while length >= 0:
        if tree[length] in ('\n', '<p>', '</p>'):
            return length + 1
        length -= 1
    return 0


def render_paragraphs(tree):
    """Walks through the nodes in the tree trying to work out where the
       correct location is to insert paragraph tags
    """

    rendered_children = []
    inside_paragraph = False

    for node_index, node in enumerate(tree):

        # Raw text
        if isinstance(node, RawText):
            if not inside_paragraph:
                paragraph_index = get_paragraph_insert_index(rendered_children)
                rendered_children.insert(paragraph_index, '<p>')
                inside_paragraph = True
            rendered_children.append(node.render())

        # Newline
        elif isinstance(node, NewlineText):
            if node.count == 1:
                rendered_children.append(node.render())
            elif node.count == 2:
                if inside_paragraph:
                    rendered_children.append('</p>')
                    inside_paragraph = False
                else:
                    rendered_children.append('<p>')
                    inside_paragraph = True

        # Any tag that can be rendered
        elif isinstance(node, BaseTag):
            if not inside_paragraph:
                rendered_children.append('<p>')
                inside_paragraph = True
            rendered_children.append(node.render())

    # If we're still inside a paragraph, close it
    if inside_paragraph:
        rendered_children.append('</p>')
        inside_paragraph = False

    return ''.join(rendered_children)


def convert_newlines(text, newline_char='\n', convert_char='<br />'):
    """Converts the new line character into the convert character
    """
    return text.replace(newline_char, convert_char)
