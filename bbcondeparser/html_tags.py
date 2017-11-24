# -*- coding: utf8 -*-
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

from __future__ import unicode_literals

import cgi
from collections import namedtuple

from . import _six as six

from .tags import (
    BaseNode, RawText, BaseTagMeta, BaseTag, NewlineText, ErrorText, RootTag)
from .tree_parser import BaseTreeParser


HTML_NEWLINE = '<br />'
NEWLINE_BEHAVIOURS = {
    None: 0,
    'convert': 1,
    'ignore': 2,
    'remove': 3,
}
PARAGRAPH_BEHAVIOURS = {
    None: 0,
    True: 1,
    False: 2,
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

    def __init__(self, *args, **kwargs):
        super(HTMLNewlineText, self).__init__(*args, **kwargs)
        self.render_mode = 'html'

    def set_html(self):
        self.render_mode = 'html'

    def set_raw(self):
        self.render_mode = 'raw'

    def set_ignore(self):
        self.render_mode = 'ignore'

    def _render(self):
        if self.render_mode == 'html':
            return '<br />'
        elif self.render_mode == 'raw':
            return self.render_raw()
        else:
            return ''


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
            ValueError: if some values are set and shouldnt
        """
        if tag_cls.newline_behaviour not in NEWLINE_BEHAVIOURS:
            raise ValueError('newline_behaviour must be one of {}'.format(
                NEWLINE_BEHAVIOURS))

        if is_inline_tag(tag_cls) and tag_cls.convert_paragraphs:
            raise ValueError(
                "Cannot enable convert_paragraphs "
                "on inline tag {tag_cls.tag_name}".format(tag_cls=tag_cls))

        if not is_inline_tag(tag_cls) and not is_block_tag(tag_cls):
            raise ValueError(
                "Unknown tag display type: {tag_cls.tag_type}"
                "on {tag_cls.tag_name}".format(tag_cls=tag_cls))


def get_newline_behaviour(current_value, new_value):
    """Return the newline behaviour based on current and new values.

    NEWLINE_BEHAVIOURS is used to store what behaviours take privaledge.

    Args:
        current_value (str): the current behaviour
        new_value (str): the potential new behaviour

    Returns:
        str: the behaviour
    """
    if NEWLINE_BEHAVIOURS[new_value] > NEWLINE_BEHAVIOURS[current_value]:
        return new_value
    else:
        return current_value


def get_convert_paragraphs(current_value, new_value):
    """Return whether we are converting paragraphs.

    PARAGRAPH_BEHAVIOURS is used to store what behaviours take privaledge.

    Args:
        current_value (None|Bool): the current value
        new_value (None|Bool): the potential new value

    Returns:
        None|Bool: the convert paragraph value
    """
    if PARAGRAPH_BEHAVIOURS[new_value] > PARAGRAPH_BEHAVIOURS[current_value]:
        return new_value
    else:
        return current_value


def get_trim_whitespace(current_value, new_value):
    """Return whether we are trimming whitespace.

    Works the same way as get_convert_paragraphs. I just couldnt think of a
    suitable name for one function that covers both.

    Args:
        current_value (None|Bool): the current value
        new_value (None|Bool): the potential value

    Returns:
        None|Bool: the convert paragraph value
    """
    return get_convert_paragraphs(current_value, new_value)


def apply_ctx(new_ctx, src_ctx):
    """Update contexts.

    Special keys such as convert_paragraphs, trim_whitespace and
    newline_behaviour have their values worked out. Anything is just
    overwritten or assigned.

    Args:
        new_ctx (dict): new context
        src_ctx (dict): source context

    Returns:
        dict: the new context
    """
    for ctx_key, ctx_value in src_ctx.items():
        if ctx_key in new_ctx:
            current_value = new_ctx[ctx_key]

            if ctx_key == 'convert_paragraphs':
                new_ctx[ctx_key] = get_convert_paragraphs(
                    current_value, ctx_value)

            elif ctx_key == 'trim_whitespace':
                new_ctx[ctx_key] = get_trim_whitespace(
                    current_value, ctx_value)

            elif ctx_key == 'newline_behaviour':
                new_ctx[ctx_key] = get_newline_behaviour(
                    current_value, ctx_value)

            else:
                new_ctx[ctx_key] = ctx_value

        else:
            new_ctx[ctx_key] = ctx_value

    return new_ctx


@six.add_metaclass(BaseHTMLTagMeta)
class BaseHTMLTag(BaseTag):
    """BaseHTMLTag, used for all HTML tags.

    Attributes:
        tag_display (str): tag display mode - block or inline
        newline_behaviour (None, str): the behaviour of newlines for this tag.
            Can be None, 'convert', 'ignore' or 'remove'.
        convert_paragraphs (None, bool): convert double newlines to paragraphs,
            can be True, False or None.
        trim_whitespace (None, bool): remove whitespace from rendered text. Can
            be True, False or None.
    """

    tag_display = 'inline'
    newline_behaviour = None
    convert_paragraphs = None
    trim_whitespace = None

    def render(self):
        """Return the rendering of this tag (including children)
            (N.B. This inherintly includes children, no way not to.
        """
        child_text = self._render()

        if self.trim_whitespace:
            child_text = child_text.strip()

        return child_text

    def get_context(self):
        return apply_ctx(
            super(BaseHTMLTag, self).get_context().copy(),
            {
                'newline_behaviour': self.newline_behaviour,
                'convert_paragraphs': self.convert_paragraphs,
            },
        )


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
        parser {newline_behaviour='convert'}
            text
            infobox {newline_behaviour='ignore'}
                text
                text
                infobox2 {newline_behaviour='convert'}
                    text
                    text
                text
            text

        should produce

        parser {newline_behaviour='convert'}
            text
            <br />
            infobox {newline_behaviour='ignore'}
                text
                text
                infobox2 {newline_behaviour='convert'}
                    text
                    text
                text
            <br />
            text

    Attributes:
        raw_text_class (RawText): type of class to use for raw text
        newline_text_class (NewlineText): type of class to use for newlines
        newline_behaviour (None, str): whether we want to ignore, remove or
            strip newlines from the text. Values can be None, 'convert',
            'remove' or 'ignore'.
        convert_paragraphs (None, bool): whether we want to convert double
            newlines into paragraphs. Values can be None, True or False.

    """

    raw_text_class = HTMLText
    newline_text_class = HTMLNewlineText
    root_tag_class = RootHTMLTag
    newline_behaviour = None
    convert_paragraphs = None

    def __init__(self, text, newline_behaviour=None, convert_paragraphs=None):
        super(BaseHTMLRenderTreeParser, self).__init__(text)

        newline_behaviour = get_newline_behaviour(
            self.newline_behaviour, newline_behaviour)
        convert_paragraphs = get_convert_paragraphs(
            self.convert_paragraphs, convert_paragraphs)

        self.root_node = amend_tree(
            self.root_node, newline_behaviour, convert_paragraphs)


def amend_tree(root_node, newline_behaviour=None, convert_paragraphs=None):
    inst = _BaseHTMLRenderTreeParser(
        root_node, newline_behaviour, convert_paragraphs)
    inst.amend_tree()
    return inst.root_node


StackLevel = namedtuple(
    'TreeParserStackLevel',
    ['tree', 'node', 'paragraph_tree', 'inside_paragraph', 'newline_behaviour',
        'convert_paragraphs']
)


class NodeStack(object):

    def __init__(self):
        self.stack = []

    def __bool__(self):
        return len(self) > 0

    __nonzero__ = __bool__

    def __len__(self):
        return len(self.stack)

    def __getitem__(self, index):
        return self.stack[index]

    def pop(self):
        return self.stack.pop()

    def push(self, *args, **kwargs):
        item = StackLevel(*args, **kwargs)
        self.stack.append(item)


class _BaseHTMLRenderTreeParser(object):

    def __init__(self, root_node, newline_behaviour=None,
                 convert_paragraphs=None):

        self.root_node = root_node
        self.stack = NodeStack()
        self.newline_behaviour = newline_behaviour
        self.convert_paragraphs = convert_paragraphs

        self._inside_paragraph = False
        self._paragraph_tree = None
        self._tree = []
        self._node = None

    def append_tree(self, item):
        self._tree.append(item)

    def append_paragraph(self, item):
        self._paragraph_tree.append(item)

    def stack_push(self):
        self.stack.push(
            self._tree, self._node, self._paragraph_tree,
            self._inside_paragraph, self.newline_behaviour,
            self.convert_paragraphs,
        )
        self._tree = []
        self._paragraph_tree = None
        self._inside_paragraph = False
        ctx = self._node.get_context()
        self.newline_behaviour = get_newline_behaviour(
            self.newline_behaviour, ctx.get('newline_behaviour'))
        self.convert_paragraphs = get_convert_paragraphs(
            self.convert_paragraphs, ctx.get('convert_paragraphs'))

    def stack_pop(self):
        self.set_state(self.stack.pop())

    def set_state(self, stack_ctx):
        self._tree = stack_ctx.tree
        self._node = stack_ctx.node
        self._paragraph_tree = stack_ctx.paragraph_tree
        self._inside_paragraph = stack_ctx.inside_paragraph
        self.newline_behaviour = stack_ctx.newline_behaviour
        self.convert_paragraphs = stack_ctx.convert_paragraphs

    @property
    def is_converting_paragraphs(self):
        return self.convert_paragraphs is True

    @property
    def is_removing_newlines(self):
        return self.newline_behaviour == 'remove'

    @property
    def is_converting_newlines(self):
        return self.newline_behaviour == 'convert'

    @property
    def is_inside_paragraph(self):
        return self._inside_paragraph is True

    def open_paragraph(self, include_node=True):
        self._inside_paragraph = True
        if include_node:
            self._paragraph_tree = [self._node]
        else:
            self._paragraph_tree = []

    def close_paragraph(self):
        # Trim any newline tags at either end of the paragraph scope
        # Convert from the left
        # ( ͡° ͜ʖ ͡°)
        for node in self._paragraph_tree:
            if isinstance(node, HTMLNewlineText):
                node.set_raw()
            else:
                break

        # Convert from the right
        # ( ͡° ͜ʖ ͡°)
        for node in self._paragraph_tree[::-1]:
            if isinstance(node, HTMLNewlineText):
                node.set_raw()
            else:
                break

        # Cha cha real smooth
        # ( ( ͜ʖ ͡° ͡°

        # When we create the ParagraphTag and assign the tree, waaay back in
        # BaseNode we are also assigning the parent to all of the children.
        paragraph_node = ParagraphTag({}, self._paragraph_tree, '', '')
        self.append_tree(paragraph_node)
        self._paragraph_tree = None
        self._inside_paragraph = False

    def handle_inline_tag(self):
        self.handle_tree()

        if self.is_converting_paragraphs:
            if not self.is_inside_paragraph:
                self.open_paragraph()
            else:
                self.append_paragraph(self._node)

        else:
            self.append_tree(self._node)

    def handle_block_tag(self):
        if self.is_inside_paragraph and self._paragraph_tree:
            self.close_paragraph()

        self.handle_tree()
        self.append_tree(self._node)

    def handle_renderable_text(self):
        if self.is_converting_paragraphs:
            if not self.is_inside_paragraph:
                # We only want to open the paragraph if the text node is not
                # only whitespace
                if not self._node.text.isspace():
                    self.open_paragraph()
            else:
                self.append_paragraph(self._node)

        else:
            self.append_tree(self._node)

    def handle_newline(self):
        # Open/close a paragraph
        if self._node.count >= 2 and self.is_converting_paragraphs:

            # Close paragraph, wrap in tag, add as node
            if self.is_inside_paragraph and self._paragraph_tree:
                self.close_paragraph()

            # Open paragraph and scope. Dont need to add node.
            else:
                self.open_paragraph(include_node=False)

        else:
            if self.is_converting_newlines:
                # we dont want to put <br/> in between blocks so
                # we actually only want to put them in paragraphs
                # if we're converting or anywhere if we're not
                # converting paragraphs
                if self.is_inside_paragraph:
                    self.append_paragraph(self._node)
                elif not self.is_converting_paragraphs:
                    self.append_tree(self._node)
                else:
                    # Not removing and not converting so change
                    # back to NewlineText
                    new_node = NewlineText(self._node.text)
                    new_node.count = self._node.count
                    self.append_tree(new_node)

            elif not self.is_removing_newlines:
                # Not removing and not converting so change back
                # to NewlineText
                self._node.set_raw()
                if self.is_inside_paragraph:
                    self.append_paragraph(self._node)
                else:
                    self.append_tree(self._node)

    def handle_tree(self):

        self.stack_push()

        for node in self._node.tree:
            self._node = node

            if is_inline_tag(self._node):
                self.handle_inline_tag()

            elif is_block_tag(self._node):
                self.handle_block_tag()

            elif isinstance(self._node, RENDERABLE_TEXT):
                self.handle_renderable_text()

            elif isinstance(self._node, NewlineText):
                self.handle_newline()

        if self.is_inside_paragraph and self._paragraph_tree:
            self.close_paragraph()

        _tree = self._tree
        self.stack_pop()
        self._node.tree = _tree

        for node in self._node.tree:
            if isinstance(node, BaseNode):
                node.set_parent_node(self._node)

    def amend_tree(self):
        self._tree = []
        self._node = self.root_node
        self._paragraph_tree = None
        self._inside_paragraph = False

        self.handle_tree()
