BB Condé Parser
===============

A portable, extensible BB Code parser written by Condé Nast Britain

Hello, World!
-------------

.. code-block:: python

    from bbcondeparser import BaseTag, BaseTreeParser

    class ExcitedTag(BaseTag):
        tag_name = 'excite'

        def _render(self):
            child_text = self.render_children()
            return '<b><i>{}</i></b>'.format(child_text)

    class Parser(BaseTreeParser):
        tags = [ExcitedTag]
        
    
    parsed = Parser("[excite]Hello, World![/excite]")
    
    print(parsed.render())


.. code-block:: shell

    >>> python hello_world.py
    <b><i>Hello, World!</i></b>
    >>>


Documentation
-------------

Further documentation is in the works, and will be present on the
`github page <https://github.com/cnduk/bbcondeparser>`_.
