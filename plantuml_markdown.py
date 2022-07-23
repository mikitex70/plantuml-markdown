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
import zlib
import string
from subprocess import Popen, PIPE
from typing import Dict, List, Optional
from zlib import adler32

from plantuml import PlantUML
import logging
import markdown
import uuid
import requests
from markdown.util import AtomicString
from xml.etree import ElementTree as etree


# use markdown_py with -v to enable warnings, or with --noisy to enable debug logs
logger = logging.getLogger('MARKDOWN')
plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))


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
        diagram = self._render_diagram(code, requested_format, base_dir)
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
                # Check for hyperlinks
                map_data = self._render_diagram(code, 'map', base_dir).decode("utf-8")
                if map_data.startswith('<map '):
                    # There are hyperlinks, add the image map
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
                img.attrib['style'] = ";".join(styles)
                img.attrib['width'] = '100%'
                if 'height' in img.attrib:
                    img.attrib.pop('height')

            img.attrib['class'] = classes
            img.attrib['alt'] = alt
            img.attrib['title'] = title

        diag_tag = etree.tostring(img, short_empty_elements=self_closed).decode()
        diag_tag = diag_tag + map_tag

        return text[:m.start()] + m.group('indent') + diag_tag + text[m.end():], \
               m.start() + len(m.group('indent')) + len(diag_tag)

    def _render_diagram(self, code, requested_format, base_dir):
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

        if diagram:
            # if cache found then end this function here
            return diagram

        # if cache not found create the diagram
        code = self._set_theme(code)

        if self.config['server']:
            diagram = self._render_remote_uml_image(code, requested_format, base_dir)
        else:
            diagram = self._render_local_uml_image(code, requested_format)

        if self.config['cachedir']:
            with open(cached_diagram_file, 'wb') as f:
                f.write(diagram)

        return diagram

    def _set_theme(self, code):
        theme = self.config['theme'].strip()

        if theme:
            # if theme configured, add it to the beginning of plantuml code
            """ These plantuml commands will result in error if theme is inserted
                skip theme insertion if present; commands are standalone, 
                hence just check beginning of plantuml code

                Handle following pattern 

                <zero more trailing spaces, newlines> 
                @startuml (optional)
                <zero more trailing spaces, newlines>
                version/stdlib/listfonts etc. (commands that error out)
                @enduml (optional)

                command list is configurable in puml_notheme_cmdlist - useful if plantuml adds new commands, 
                otherwise will need to update this code every time!
            """

            puml_notheme_cmdlist = self.config['puml_notheme_cmdlist']

            startuml = "@startuml\n"
            code = code.lstrip().lstrip('\n')
            startuml_present = code.startswith(startuml)

            # first remove startuml tag if present
            if startuml_present:
                code_nostartuml = code[len(startuml):].lstrip().lstrip('\n')
            else:
                code_nostartuml = code

            # validate that troublesome commands are not present
            theme_wont_err = not code_nostartuml.startswith(tuple(puml_notheme_cmdlist))

            # then add theme appropriately
            if startuml_present and theme_wont_err:
                # add it after the @startuml tag
                code = startuml + "!theme " + theme + "\n" + code_nostartuml
            elif theme_wont_err:
                # if no @startuml tag found just add it to the beginning
                code = "\n!theme " + theme + "\n" + code

        return code

    @staticmethod
    def _render_local_uml_image(plantuml_code, img_format):
        plantuml_code = plantuml_code.encode('utf8')
        cmdline = ['plantuml', '-pipemap' if img_format == 'map' else '-p', "-t" + img_format]

        try:
            # On Windows run batch files through a shell so the extension can be resolved
            p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=(os.name == 'nt'))
            out, err = p.communicate(input=plantuml_code)

        except Exception as exc:
            raise Exception('Failed to run plantuml: %s' % exc)
        else:
            if p.returncode != 0:
                # plantuml returns a nice image in case of syntax error so log but still return out
                logger.error('Error in "uml" directive: %s' % err)

            return out

    def _render_remote_uml_image(self, plantuml_code, img_format, base_dir):
        # build the whole source diagram, executing include directives
        temp_file = PlantUMLIncluder(False).readFile(plantuml_code, base_dir)
        http_method = self.config['http_method'].strip()
        fallback_to_get = self.config['fallback_to_get']
    
        # Use GET if preferred, use POST with GET as fallback if POST fails
        post_failed = False

        if http_method == "POST":
            # image_url for POST attempt first
            image_url = "%s/%s/" % (self.config['server'], img_format)
            # download manually the image to be able to continue in case of errors

            with requests.post(image_url, data=temp_file, headers={"Content-Type": 'text/plain; charset=utf-8'}) as r:
                if not r.ok:
                    logger.warning('WARNING in "uml" directive: remote server has returned error %d on POST' % r.status_code)
                    if fallback_to_get:
                        logger.error('Falling back to Get')
                        post_failed = True
                if not post_failed:
                    return r.content

        if http_method == "GET" or post_failed:
            image_url = self.config['server']+"/"+img_format+"/"+self._deflate_and_encode(temp_file)

            with requests.get(image_url) as r:
                if not r.ok:
                    logger.warning('WARNING in "uml" directive: remote server has returned error %d on GET' % r.status_code)

            return r.content

    @staticmethod
    def _deflate_and_encode(source: str) -> str:
        # algorithm borrowed from the plantuml package
        zlibbed_str = zlib.compress(source.encode('utf-8'))

        return base64.b64encode(zlibbed_str[2:-4]).translate(b64_to_plantuml).decode('utf-8')


class PlantUMLIncluder:

    def __init__(self, dark_mode: bool, light_theme: Optional[str] = None, dark_theme: Optional[str] = None):
        self._dark_mode = dark_mode
        self._light_theme = light_theme
        self._dark_theme = dark_theme
        self._definitions: Dict[str, str] = {}

    # Given a PlantUML source, replace any "!include" directive with the included code, recursively
    def readFile(self, plantuml_code: str, directory: str) -> str:
        lines = plantuml_code.splitlines()
        # Wrap the whole combined text between startuml and enduml tags as recursive processing would have removed them
        # This is necessary for it to work correctly with plamtuml POST processing
        return "@startuml\n" + "\n".join(self._readFileRec(lines, directory)) + "@enduml\n"

    # Reads the file recursively
    def _readFileRec(self, lines: List[str], directory: str) -> List[str]:
        result: List[str] = []

        for line in lines:
            line = line.strip()

            # preprocessor, define variable, new syntax
            match = re.search(r'!(?P<varname>\$?\w+)\s+=\s+"(?P<value>.*)"', line)

            if not match:
                # preprocessor, define variable, old syntax
                match = re.search(r'^!define (?P<varname>\w+)\s+(?P<value>.*)', line)

            if match:
                # variable definition, save the mapping as the value can be used in !include directives
                self._definitions[match.group('varname')] = match.group('value')
                result.append(line)
            elif line.startswith("!include"):
                result.append(self._readInclLine(line, directory))
            elif line.startswith("@startuml") or line.startswith("@enduml"):
                # remove startuml and enduml tags as plantuml POST method doesn't like it in include files
                # we will wrap the whole combined text between start and end tags at the end
                continue
            else:
                result.append(line)

        return result

    def _readInclLine(self, line: str, directory: str) -> str:
        # If includeurl is found, we do not have to do anything here. Server can handle that
        if "!includeurl" in line:
            return line

        # on the ninth position starts the filename
        inc_file = line[9:].rstrip()

        for varname, value in self._definitions.items():
            if inc_file.startswith(varname):
                inc_file = inc_file.replace(varname, value)
                break

        if self._dark_mode:
            inc_file = inc_file.replace(self._light_theme, self._dark_theme)

        # According to plantuml, simple !include can also have urls, or use the <> format to include stdlib files,
        # ignore that and continue
        if inc_file.startswith("http") or inc_file.startswith("<"):
            return line

        # Read contents of the included file
        try:
            inc_file_abs = os.path.normpath(os.path.join(directory, inc_file))
            return self._read_incl_line_file(inc_file_abs)
        except Exception as e1:
            logger.error("Could not find include " + str(e1))
            raise e1

    def _read_incl_line_file(self, inc_file_abs: str):
        with open(inc_file_abs, "r") as inc:
            return "\n".join(self._readFileRec(inc.readlines(), os.path.dirname(os.path.realpath(inc_file_abs))))


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
            'encoding': ["utf8", "Default character encoding for external files (default: utf8)"],
            'http_method': ["GET", "Http Method for server - GET or POST", "Defaults to GET"],
            'fallback_to_get': [True, "Fallback to GET if POST fails", "Defaults to True"],
            'theme': ["", "Default Theme to use, will be overridden  by !theme directive", "Defaults to blank"],
            'puml_notheme_cmdlist': [[
                                     'version', 
                                     'listfonts', 
                                     'stdlib', 
                                     'license'
                                     ], 
                                     "theme will not be set if listed commands present (default list),",
                                     "Defaults to the before mentioned list"
                                    ]
        }

        # Fix to make links navigable in SVG diagrams
        etree.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

        super(PlantUMLMarkdownExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
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
