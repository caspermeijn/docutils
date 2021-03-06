#!/usr/bin/env python
# -*- coding: utf8 -*-
# :Copyright: © 2020 Günter Milde.
# :License: Released under the terms of the `2-Clause BSD license`_, in short:
#
#    Copying and distribution of this file, with or without modification,
#    are permitted in any medium without royalty provided the copyright
#    notice and this notice are preserved.
#    This file is offered as-is, without any warranty.
#
# .. _2-Clause BSD license: https://opensource.org/licenses/BSD-2-Clause
#
# Revision: $Revision$
# Date: $Date$
"""
A parser for CommonMark MarkDown text using `recommonmark`__.

__ https://pypi.org/project/recommonmark/
"""

import docutils.parsers
from docutils import nodes

try:
    from recommonmark.parser import CommonMarkParser as _recommonmarkParser
    _recommonmarkParser.supported = ('recommonmark', 'commonmark',
                                     'markdown', 'md')
    with_recommonmark = True
except ImportError as err:
    with_recommonmark = False
    class _recommonmarkParser(docutils.parsers.Parser):
        def parse(self, inputstring, document):
            error = document.reporter.warning(
                'Missing dependency: MarkDown input is processed by a 3rd '
                'party parser but Python did not find the required module '
                '"recommonmark" (https://pypi.org/project/recommonmark/).')
            document.append(error)

class Parser(_recommonmarkParser):
    config_section = 'recommonmark parser'
    config_section_dependencies = ('parsers',)

    def parse(self, inputstring, document):
        """Use the upstream parser and clean up afterwards.
        """
        # check for exorbitantly long lines
        for i, line in enumerate(inputstring.split('\n')):
            if len(line) > document.settings.line_length_limit:
                error = document.reporter.error(
                    'Line %d exceeds the line-length-limit.'%(i+1))
                document.append(error)
                return

        # pass to upstream parser
        try:
            _recommonmarkParser.parse(self, inputstring, document)
        except Exception as err:
            error = document.reporter.error('Parsing with "recommonmark" '
                                            'returned the error:\n%s'%err)
            document.append(error)

        # Post-Processing
        # ---------------

        # merge adjoining Text nodes:
        for node in document.traverse(nodes.TextElement):
            children = node.children
            i = 0
            while i+1 < len(children):
                if (isinstance(children[i], nodes.Text)
                    and isinstance(children[i+1], nodes.Text)):
                    children[i] = nodes.Text(children[i]+children.pop(i+1))
                    children[i].parent = node
                else:
                    i += 1

        # add "code" class argument to inline literal (code spans)
        for node in document.traverse(lambda n: isinstance(n,
                                (nodes.literal, nodes.literal_block))):
            node['classes'].append('code')
        # move "language" argument to classes
        for node in document.traverse(nodes.literal_block):
            if 'language' in node.attributes:
                node['classes'].append(node['language'])
                del node['language']

        # remove empty target nodes
        for node in document.traverse(nodes.target):
            # remove empty name
            node['names'] = [v for v in node['names'] if v]
            if node.children or [v for v in node.attributes.values() if v]:
                continue
            node.parent.remove(node)

        # replace raw nodes if raw is not allowed
        if not document.settings.raw_enabled:
            for node in document.traverse(nodes.raw):
                warning = document.reporter.warning('Raw content disabled.')
                node.parent.replace(node, warning)

        # fix section nodes
        for node in document.traverse(nodes.section):
            # remove spurious IDs (first may be from duplicate name)
            if len(node['ids']) > 1:
                node['ids'].pop()
            # fix section levels
            section_level = self.get_section_level(node)
            if node['level'] != section_level:
                warning = document.reporter.warning(
                    'Title level inconsistent. Changing from %d to %d.'
                    %(node['level'], section_level),
                    nodes.literal_block('', node[0].astext()))
                node.insert(1, warning)
            # remove non-standard attribute "level"
            del node['level'] # TODO: store the original md level somewhere

    def get_section_level(self, node):
        level = 1
        while True:
            node = node.parent
            if isinstance(node, nodes.document):
                return level
            if isinstance(node, nodes.section):
                level += 1
