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


   Supported values for `format` parameter are:

   * `png`: HTML `img` tag with embedded png image
   * `svg`: HTML `img` tag with embedded svg image (links are not navigable)
   * `svg_object`: HTML `object` tag with embedded svg image (links are navigable)
   * `svg_inline`: HTML5 `svg` tag with inline svg image source (links are navigable, can be manipulated with CSS rules)
   * `txt`: plain text diagrams.
   
   For more details see the [GitHub repository](https://github.com/mikitex70/plantuml-markdown).

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
   (recommended).

   [Python-Markdown]: http://pythonhosted.org/Markdown/
   [PlantUML]: http://plantuml.sourceforge.net/
   [Graphviz]: http://www.graphviz.org
   [Gentoo]: http://www.gentoo.org
   [layman]: http://wiki.gentoo.org/wiki/Layman
"""

import os
import re
import base64
from subprocess import Popen, PIPE
from plantuml import PlantUML
import logging
import markdown
from markdown.util import etree, AtomicString


logger = logging.getLogger('MARKDOWN')
logger.setLevel(logging.DEBUG)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#blockparser
class PlantUMLPreprocessor(markdown.preprocessors.Preprocessor):
    # Regular expression inspired from fenced_code
    BLOCK_RE = re.compile(r'''
        ::uml:: 
        # args
        \s*(format=(?P<quot>"|')(?P<format>\w+)(?P=quot))?
        \s*(classes=(?P<quot1>"|')(?P<classes>[\w\s]+)(?P=quot1))?
        \s*(alt=(?P<quot2>"|')(?P<alt>[\w\s"']+)(?P=quot2))?
        \s*(title=(?P<quot3>"|')(?P<title>[\w\s"']+)(?P=quot3))?
        \s*(width=(?P<quot4>"|')(?P<width>[\w\s"']+)(?P=quot4))?
        \s*(height=(?P<quot5>"|')(?P<height>[\w\s"']+)(?P=quot5))?
        \s*\n
        (?P<code>.*?)(?<=\n)
        ::end-uml::[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    FENCED_BLOCK_RE = re.compile(r'''
        (?P<fence>^(?:~{3,}|`{3,}))[ ]*         # Opening ``` or ~~~
        (\{?\.?(plant)?uml)[ ]*                 # Optional {, and lang
        # args
        \s*(format=(?P<quot>"|')(?P<format>\w+)(?P=quot))?
        \s*(classes=(?P<quot1>"|')(?P<classes>[\w\s]+)(?P=quot1))?
        \s*(alt=(?P<quot2>"|')(?P<alt>[\w\s"']+)(?P=quot2))?
        \s*(title=(?P<quot3>"|')(?P<title>[\w\s"']+)(?P=quot3))?
        \s*(width=(?P<quot4>"|')(?P<width>[\w\s"']+)(?P=quot4))?
        \s*(height=(?P<quot5>"|')(?P<height>[\w\s"']+)(?P=quot5))?
        [ ]*
        }?[ ]*\n                                # Optional closing }
        (?P<code>.*?)(?<=\n)
        (?P=fence)[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super(PlantUMLPreprocessor, self).__init__(md)

    def run(self, lines):
        text = '\n'.join(lines)
        did_replace = True

        while did_replace:
            text, did_replace = self._replace_block(text)

        return text.split('\n')

    # regex for removing some parts from the plantuml generated svg
    ADAPT_SVG_REGEX = re.compile(r'^<\?xml .*?\?><svg(.*?)xmlns=".*?" (.*?)>')

    def _replace_block(self, text):
        # Parse configuration params
        m = self.FENCED_BLOCK_RE.search(text)
        if not m:
            m = self.BLOCK_RE.search(text)
            if not m:
                return text, False

        # Parse configuration params
        img_format = m.group('format') if m.group('format') else self.config['format']
        classes = m.group('classes') if m.group('classes') else self.config['classes']
        alt = m.group('alt') if m.group('alt') else self.config['alt']
        title = m.group('title') if m.group('title') else self.config['title']
        width = m.group('width') if m.group('width') else None
        height = m.group('height') if m.group('height') else None

        # Convert image type in PlantUML image format
        if img_format == 'png':
            requested_format = "png"
        elif img_format in ['svg', 'svg_object', 'svg_inline']:
            requested_format = "svg"
        elif img_format == 'txt':
            requested_format = "txt"
        else:
            # logger.error("Bad uml image format '"+imgformat+"', using png")
            requested_format = "png"

        # Extract diagram source end convert it
        code = m.group('code')

        if self.config['server']:
            diagram = self._render_remote_uml_image(code, requested_format)
        else:
            diagram = self._render_local_uml_image(code, requested_format)
        
        if img_format == 'txt':
            # logger.debug(diagram)
            img = etree.Element('pre')
            code = etree.SubElement(img, 'code')
            code.attrib['class'] = 'text'
            code.text = AtomicString(diagram.decode('UTF-8'))
        else:
            # These are images
            if img_format == 'svg_inline':
                data = self.ADAPT_SVG_REGEX.sub('<svg \\1\\2>', diagram.decode('UTF-8'))
                img = etree.fromstring(data.encode('UTF-8'))
                # remove width and height in style attribute
                img.attrib['style'] = re.sub(r'\b(?:width|height):\d+px;', '', img.attrib['style'])
            elif img_format == 'svg':
                # Firefox handles only base64 encoded SVGs
                data = 'data:image/svg+xml;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
                img = etree.Element('img')
                img.attrib['src'] = data
            elif img_format == 'svg_object':
                # Firefox handles only base64 encoded SVGs
                data = 'data:image/svg+xml;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
                img = etree.Element('object')
                img.attrib['data'] = data
            else:  # png format, explicitly set or as a default when format is not recognized
                data = 'data:image/png;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
                img = etree.Element('img')
                img.attrib['src'] = data

            styles = []
            if width:
                styles.append("max-width:"+width)
            if height:
                styles.append("max-height:"+height)

            if styles:
                style = img.attrib['style']+';' if 'style' in img.attrib and img.attrib['style'] != '' else ''
                img.attrib['style'] = style+";".join(styles)
                img.attrib['width'] = '100%'
                if 'height' in img.attrib:
                    img.attrib.pop('height')

            img.attrib['class'] = classes
            img.attrib['alt'] = alt
            img.attrib['title'] = title

        return text[:m.start()] + etree.tostring(img).decode() + text[m.end():], True

    @staticmethod
    def _render_local_uml_image(plantuml_code, img_format):
        plantuml_code = plantuml_code.encode('utf8')
        cmdline = ['plantuml', '-p', "-t" + img_format]

        try:
            # On Windows run batch files through a shell so the extension can be resolved
            p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=(os.name == 'nt'))
            out, err = p.communicate(input=plantuml_code)
        except Exception as exc:
            raise Exception('Failed to run plantuml: %s' % exc)
        else:
            if p.returncode != 0:
                # plantuml returns a nice image in case of syntax error so log but still return out
                print('Error in "uml" directive: %s' % err)

            return out

    def _render_remote_uml_image(self, plantuml_code, img_format):
        return PlantUML("%s/%s/" % (self.config['server'], img_format)).processes(plantuml_code)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#extendmarkdown
class PlantUMLMarkdownExtension(markdown.Extension):
    # For details see https://pythonhosted.org/Markdown/extensions/api.html#configsettings
    def __init__(self, **kwargs):
        self.config = {
            'classes': ["uml", "Space separated list of classes for the generated image. Defaults to 'uml'."],
            'alt': ["uml diagram", "Text to show when image is not available. Defaults to 'uml diagram'"],
            'format': ["png", "Format of image to generate (png, svg or txt). Defaults to 'png'."],
            'title': ["", "Tooltip for the diagram"],
            'server': ["", "PlantUML server url, for remote rendering. Defaults to '', use local command."],
        }

        # Fix to make links navigable in SVG diagrams
        etree.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

        super(PlantUMLMarkdownExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        blockprocessor = PlantUMLPreprocessor(md)
        blockprocessor.config = self.getConfigs()
        # need to go before both fenced_code_block and things like retext's PosMapMarkPreprocessor.
        # Need to go after mdx_include.
        md.preprocessors.register(blockprocessor, 'plantuml', 100)


def makeExtension(**kwargs):
    return PlantUMLMarkdownExtension(**kwargs)
