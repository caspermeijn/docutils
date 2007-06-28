#!/usr/bin/env python

# :Author: Guenter Milde
# :Contact: 
# :Revision: $Revision$
# :Date: $Date$
# :Copyright: Licensed under the Academic Free License version 1.2

"""
Front end to the Docutils Publisher, producing readable LaTeX2e.

Variant with compulsory style sheet 
"""

# prepend parent dir to the PYTHONPATH
import sys
sys.path.insert(0, '..')

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description

# import the writer variant
from latex2e_external_stylesheet import Writer

description = ('Experimental "latex2e" writer variant'
               + default_description)

publish_cmdline(writer=Writer(), description=description)
