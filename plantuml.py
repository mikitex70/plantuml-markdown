#!/usr/bin/env python
"""
   [PlantUML][] Extension for [Python-Markdown][]
   ==============================================

   This plugin implements a block extension which can be used to specify a [PlantUML][] diagram which will be
   converted into an image and inserted in the document.

   Syntax:

      ::uml:: [format="png|svg"] [classes="class1 class2 ..."] [alt="text for alt"]
          PlantUML script diagram
      ::end-uml::

   Example:

      ::uml:: format="png" classes="uml myDiagram" alt="My super diagram"
          Goofy ->  MickeyMouse: calls
          Goofy <-- MickeyMouse: responds
      ::end-uml::

   Options are optional, but if present must be specified in the order format, classes, alt.
   The option value may be enclosed in single or double quotes.

   Installation
   ------------
   You need to install [PlantUML][] (see the site for details) and [Graphviz][] 2.26.3 or later.
   The plugin expects a program `plantuml` in the classpath. If not installed by your package
   manager, you can create a shell script and place it somewhere in the classpath. For example,
   save te following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
   `/opt/plantuml`):

       #!/bin/bash
       java -jar /opt/plantuml/plantuml.jar ${@}

   For [Gentoo Linux][Gentoo] there is an ebuild at http://gpo.zugaina.org/dev-util/plantuml/RDep: you can download
   the ebuild and the `files` subfolder or you can add the `zugaina` repository with [layman][]
   (reccomended).

   [Python-Markdown]: http://pythonhosted.org/Markdown/
   [PlantUML]: http://plantuml.sourceforge.net/
   [Graphviz]: http://www.graphviz.org
   [Gentoo]: http://www.gentoo.org
   [layman]: http://wiki.gentoo.org/wiki/Layman
"""

import os
import re
import base64
import tempfile
from subprocess import Popen, PIPE
from zlib import adler32
import logging
import markdown
from markdown.util import etree, AtomicString


#logger = logging.getLogger('MARKDOWN')
#logger.setLevel(logging.DEBUG)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#blockparser
class PlantUMLBlockProcessor(markdown.blockprocessors.BlockProcessor):
    # Regular expression inspired by the codehilite Markdown plugin
    RE = re.compile(r'''\s*(?P<delimiter>(::uml::)|(```(plant)?uml))
                        \s*(format=(?P<quot>"|')(?P<format>\w+)(?P=quot))?
                        \s*(classes=(?P<quot1>"|')(?P<classes>[\w\s]+)(?P=quot1))?
                        \s*(alt=(?P<quot2>"|')(?P<alt>[\w\s"']+)(?P=quot2))?
                        \s*(title=(?P<quot3>"|')(?P<title>[\w\s"']+)(?P=quot3))?
                    ''', re.VERBOSE+re.UNICODE)
    # Regular expression for identify end of UML script
    RE_END1 = re.compile(r'.*::end-uml::')
    RE_END2 = re.compile(r'.*```$')

    def test(self, parent, block):
        return self.RE.search(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        text = block

        # Parse configuration params
        m = self.RE.search(block)
        delimiter = m.group('delimiter')
        imgformat = m.group('format') if m.group('format') else self.config['format']
        classes = m.group('classes') if m.group('classes') else self.config['classes']
        alt = m.group('alt') if m.group('alt') else self.config['alt']
        title = m.group('title') if m.group('title') else self.config['title']

        # Read blocks until end marker found
        end_re = self.RE_END1 if delimiter == '::uml::' else self.RE_END2

        while blocks and not end_re.search(block):
            block = blocks.pop(0)
            text += '\n' + block
        else:
            if not blocks:
                raise RuntimeError("UML block not closed")

        # Remove block header and footer
        text = re.sub(self.RE, "", re.sub(end_re, "", text))
        text = "\n".join(text.split('\n'))
        diagram = self.generate_uml_image(text, imgformat)
        
        p = etree.SubElement(parent, 'p')
        if imgformat == 'png':
            data = 'data:image/png;base64,{0}'.format(
                base64.b64encode(diagram).decode('ascii')
            )
            img = etree.SubElement(p, 'img')
            img.attrib['src'    ] = data
            img.attrib['classes'] = classes
            img.attrib['alt'    ] = alt
            img.attrib['title'  ] = title
        elif imgformat == 'svg':
            # Firefox handles only base64 encoded SVGs
            data = 'data:image/svg+xml;base64,{0}'.format(
                base64.b64encode(diagram).decode('ascii')
            )
            img = etree.SubElement(p, 'img')
            img.attrib['src'    ] = data
            img.attrib['classes'] = classes
            img.attrib['alt'    ] = alt
            img.attrib['title'  ] = title
        elif imgformat == 'txt':
            #logger.debug(diagram)
            pre = etree.SubElement(parent, 'pre')
            code = etree.SubElement(pre, 'code')
            code.attrib['class'] = 'text'
            code.text = AtomicString(diagram)

    @staticmethod
    def generate_uml_image(plantuml_code, imgformat):
        if imgformat == 'png':
            outopt = "-tpng"
        elif imgformat == 'svg':
            outopt = "-tsvg"
        elif imgformat == 'txt':
            outopt = "-ttxt"
        else:
            logger.error("Bad uml image format '"+imgformat+"', using png")
            outopt = "-tpng"

        plantuml_code = plantuml_code.encode('utf8')
        
        cmdline = ['plantuml', '-p', outopt ]

        try:
            p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate(input=plantuml_code)
        except Exception as exc:
            raise Exception('Failed to run plantuml: %s' % exc)
        else:
            if p.returncode == 0:
                return out
            else:
                raise RuntimeError('Error in "uml" directive: %s' % err)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#extendmarkdown
class PlantUMLMarkdownExtension(markdown.Extension):
    # For details see https://pythonhosted.org/Markdown/extensions/api.html#configsettings
    def __init__(self, *args, **kwargs):
        self.config = {
            'classes': ["uml", "Space separated list of classes for the generated image. Defaults to 'uml'."],
            'alt': ["uml diagram", "Text to show when image is not available. Defaults to 'uml diagram'"],
            'format': ["png", "Format of image to generate (png, svg or txt). Defaults to 'png'."],
            'title': ["", "Tooltip for the diagram"]
        }

        super(PlantUMLMarkdownExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        blockprocessor = PlantUMLBlockProcessor(md.parser)
        blockprocessor.config = self.getConfigs()
        md.parser.blockprocessors.add('plantuml', blockprocessor, '>code')


def makeExtension(*args, **kwargs):
    return PlantUMLMarkdownExtension(*args, **kwargs)
