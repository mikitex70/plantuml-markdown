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
from zlib import adler32

from plantuml import PlantUML
import logging
import markdown
import uuid
from markdown.util import AtomicString
from xml.etree import ElementTree as etree


logger = logging.getLogger('MARKDOWN')
# logger.setLevel(logging.DEBUG)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#blockparser
class PlantUMLPreprocessor(markdown.preprocessors.Preprocessor):
    # Regular expression inspired from fenced_code
    BLOCK_RE = re.compile(r'''
        (?P<indent>[ ]*)
        ::uml:: 
        # args
        \s*(format=(?P<quot>"|')(?P<format>\w+)(?P=quot))?
        \s*(classes=(?P<quot1>"|')(?P<classes>[\w\s]+)(?P=quot1))?
        \s*(alt=(?P<quot2>"|')(?P<alt>.*?)(?P=quot2))?
        \s*(title=(?P<quot3>"|')(?P<title>.*?)(?P=quot3))?
        \s*(width=(?P<quot4>"|')(?P<width>[\w\s"']+%?)(?P=quot4))?
        \s*(height=(?P<quot5>"|')(?P<height>[\w\s"']+%?)(?P=quot5))?
        \s*(source=(?P<quot6>"|')(?P<source>.*?)(?P=quot6))?
        \s*\n
        (?P<code>.*?)(?<=\n)
        (?P=indent)::end-uml::[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    FENCED_BLOCK_RE = re.compile(r'''
        (?P<indent>[ ]*)
        (?P<fence>(?:~{3}|`{3}))[ ]*            # Opening ``` or ~~~
        (\{?\.?(plant)?uml)[ ]*                 # Optional {, and lang
        # args
        \s*(format=(?P<quot>"|')(?P<format>\w+)(?P=quot))?
        \s*(classes=(?P<quot1>"|')(?P<classes>[\w\s]+)(?P=quot1))?
        \s*(alt=(?P<quot2>"|')(?P<alt>.*?)(?P=quot2))?
        \s*(title=(?P<quot3>"|')(?P<title>.*?)(?P=quot3))?
        \s*(width=(?P<quot4>"|')(?P<width>[\w\s"']+%?)(?P=quot4))?
        \s*(height=(?P<quot5>"|')(?P<height>[\w\s"']+%?)(?P=quot5))?
        \s*(source=(?P<quot6>"|')(?P<source>.*?)(?P=quot6))?
        [ ]*
        }?[ ]*\n                                # Optional closing }
        (?P<code>.*?)(?<=\n)
        (?P=indent)(?P=fence)[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)
    # (?P<indent>[ ]*)(?P<fence>(?:~{3}|`{3}))[ ]*(\{?\.?(plant)?uml)[ ]*\n(?P<code>.*?)(?<=\n)(?P=indent)(?P=fence)$
    FENCED_CODE_RE = re.compile(r'(?P<fence>(?:~{4,}|`{4,})).*?(?P=fence)',
                                re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super(PlantUMLPreprocessor, self).__init__(md)

    def run(self, lines):
        text = '\n'.join(lines)
        idx = 0

        # loop until all text is parsed
        while idx < len(text):
            text1, idx1 = self._replace_block(text[idx:])
            text = text[:idx]+text1
            idx += idx1

        return text.split('\n')

    # regex for removing some parts from the plantuml generated svg
    ADAPT_SVG_REGEX = re.compile(r'^<\?xml .*?\?><svg(.*?)xmlns=".*?" (.*?)>')

    def _replace_block(self, text):
        # skip fenced code enclosing diagram
        m = self.FENCED_CODE_RE.search(text)
        if m:
            # check if before the fenced code there is a plantuml diagram
            m1 = self.FENCED_BLOCK_RE.search(text[:m.start()])
            if m1 is None:
                # no diagram, skip this block of text
                return text, m.end()+1

        # Parse configuration params
        m = self.FENCED_BLOCK_RE.search(text)
        if not m:
            m = self.BLOCK_RE.search(text)
            if not m:
                return text, len(text)

        # Parse configuration params
        img_format = m.group('format') if m.group('format') else self.config['format']
        classes = m.group('classes') if m.group('classes') else self.config['classes']
        alt = m.group('alt') if m.group('alt') else self.config['alt']
        title = m.group('title') if m.group('title') else self.config['title']
        width = m.group('width') if m.group('width') else None
        height = m.group('height') if m.group('height') else None
        source = m.group('source') if m.group('source') else None

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

        # Extract the PlantUML code.
        code = ""
        base_dir = self.config['base_dir'] if self.config['base_dir'] else None
        encoding = self.config['encoding'] if self.config['encoding'] else 'utf8'
        # Add external diagram source.
        if source and base_dir:
            with open(os.path.join(base_dir, source), 'r', encoding=encoding) as f:
                code += f.read()
        # Add extracted markdown diagram text.
        code += m.group('code')

        # Extract diagram source end convert it (if not external)
        diagram = self._render_diagram(code, requested_format)
        self_closed = True  # tags are always self closing

        map_tag = ''
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
                self_closed = False  # object tag must be explicitly closed
            else:  # png format, explicitly set or as a default when format is not recognized
                data = 'data:image/png;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
                img = etree.Element('img')
                img.attrib['src'] = data

                if self.config['server'] == '':  # local diagram rendering
                    # Add map for hyperlink
                    map_data = self._render_local_uml_map(code, requested_format).decode("utf-8")
                    if len(map_data) > 1:
                        unique_id = str(uuid.uuid4())
                        map = etree.fromstring(map_data)
                        map.attrib['id'] = unique_id
                        map.attrib['name'] = unique_id
                        map_tag = etree.tostring(map, short_empty_elements=self_closed).decode()
                        img.attrib['usemap'] = '#' + unique_id

            styles = []
            if 'style' in img.attrib and img.attrib['style'] != '':
                styles.append(re.sub(r';$', '', img.attrib['style']))
            if width:
                styles.append("max-width:"+width)
            if height:
                styles.append("max-height:"+height)

            if styles:
                img.attrib['style'] = ";".join(styles) #style+";".join(styles)
                img.attrib['width'] = '100%'
                if 'height' in img.attrib:
                    img.attrib.pop('height')

            img.attrib['class'] = classes
            img.attrib['alt'] = alt
            img.attrib['title'] = title

        diag_tag = etree.tostring(img, short_empty_elements=self_closed).decode()
        diag_tag = map_tag + diag_tag

        return text[:m.start()] + m.group('indent') + diag_tag + text[m.end():], \
               m.start() + len(m.group('indent')) + len(diag_tag)

    def _render_diagram(self, code, requested_format):
        cached_diagram_file = None
        diagram = None

        if self.config['cachedir']:
            diagram_hash = "%08x" % (adler32(code.encode('UTF-8')) & 0xffffffff)
            cached_diagram_file = os.path.expanduser(
                    os.path.join(
                        self.config['cachedir'],
                        diagram_hash + '.' + requested_format))

            if os.path.isfile(cached_diagram_file):
                with open(cached_diagram_file, 'rb') as f:
                    diagram = f.read()

        if not diagram:
            if self.config['server']:
                diagram = self._render_remote_uml_image(code, requested_format)
            else:
                diagram = self._render_local_uml_image(code, requested_format)

            if self.config['cachedir']:
                with open(cached_diagram_file, 'wb') as f:
                    f.write(diagram)

        return diagram

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

    @staticmethod
    def _render_local_uml_map(plantuml_code, img_format):
        plantuml_code = plantuml_code.encode('utf-8')
        cmdline = ['plantuml', '-pipemap', '-t' + img_format]

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
            'cachedir': ["", "Directory for caching of diagrams. Defaults to '', no caching"],
            'priority': ["30", "Extension priority. Higher values means the extension is applied sooner than others. "
                               "Defaults to 30"],
            'base_dir': [".", "Base directory for external files inclusion"],
            'encoding': ["utf8", "Default character encoding for external files (default: utf8)"]
        }

        # Fix to make links navigable in SVG diagrams
        etree.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

        super(PlantUMLMarkdownExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md, md_globals=None):
        blockprocessor = PlantUMLPreprocessor(md)
        blockprocessor.config = self.getConfigs()
        # need to go before both fenced_code_block and things like retext's PosMapMarkPreprocessor.
        # Need to go after mdx_include.
        if markdown.__version_info__[0] < 3:
            md.preprocessors.add('plantuml', blockprocessor, '_begin')
        else:
            md.preprocessors.register(blockprocessor, 'plantuml', int(blockprocessor.config['priority']))


def makeExtension(**kwargs):
    return PlantUMLMarkdownExtension(**kwargs)
