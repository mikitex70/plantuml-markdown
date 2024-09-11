#!/usr/bin/env python
"""
   [PlantUML][] Extension for [Python-Markdown][]
   ==============================================

   This plugin implements a block extension which can be used to specify a [PlantUML][] diagram which will be
   converted into an image and inserted in the document.

   Syntax (as used in Pelican):

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
   save the following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
   `/opt/plantuml`):

       #!/bin/bash
       java -jar /opt/plantuml/plantuml.jar ${@}

   For [Gentoo Linux][Gentoo] there is an ebuild at http://gpo.zugaina.org/dev-util/plantuml/RDep: you can download
   the ebuild and the `files` subfolder or you can add the `zugaina` repository with [layman][]
   (recommended).

   [Python-Markdown]: https://python-markdown.github.io
   [PlantUML]: https://plantuml.com
   [Graphviz]: http://www.graphviz.org
   [Gentoo]: http://www.gentoo.org
   [layman]: http://wiki.gentoo.org/wiki/Layman
"""

import os
import re
import base64
import zlib
import string
import urllib3
from subprocess import Popen, PIPE
from typing import Dict, List, Optional, Tuple
from zlib import adler32

import logging
import markdown
import uuid
import requests
from markdown.util import AtomicString
from requests import Session
from requests.adapters import HTTPAdapter, Retry, Response
from xml.etree import ElementTree as etree



# use markdown_py with -v to enable warnings, or with --noisy to enable debug logs
logger = logging.getLogger('MARKDOWN')
plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))


# For details see https://python-markdown.github.io/extensions/api/#blockparser
class PlantUMLPreprocessor(markdown.preprocessors.Preprocessor):
    # Regular expression inspired from fenced_code
    BLOCK_RE = re.compile(r'''
        (?P<indent>[ ]*)
        (?P<lang>::uml::) 
        # args
        \s*(id=(?P<quot7>"|')(?P<id>[-\w]+?)(?P=quot7))?
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
        (?P<fence>(?:~{3}|`{3}))[ ]*               # Opening ``` or ~~~
        (\{?\.?(?P<lang>((?:c4)?plant)?uml))[ ]*   # Optional {, and lang
        # args
        \s*(id=(?P<quot7>"|')(?P<id>[-\w]+?)(?P=quot7))?
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
    FENCED_CODE_RE = re.compile(r'(?P<fence>(~{4,}|`{4,})).*?(?P=fence)',
                                re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super(PlantUMLPreprocessor, self).__init__(md)
        self._cachedir: Optional[str] = None
        self._plantuml_server: Optional[str] = None
        self._kroki_server: Optional[str] = None
        self._base_dir: Optional[List[str]] = None
        self._encoding: str = 'utf-8'
        self._http_method: str = 'GET'
        self._fallback_to_get: bool = True
        self._config_path: Optional[str] = None

    def run(self, lines: List[str]) -> List[str]:
        # extract some configurations, to simplify code
        self._cachedir = self.config['cachedir']
        self._plantuml_server = self.config['server']
        self._kroki_server = self.config['kroki_server']
        self._encoding = self.config['encoding'] or self._encoding
        self._http_method = self.config['http_method'].strip()
        self._fallback_to_get = bool(self.config['fallback_to_get'])
        self._base_dir = self.config['base_dir']

        if not isinstance(self._base_dir, list):
            self._base_dir = [self._base_dir]

        # make sure they are strings (can be DocsDirPlaceholder is !relative is used in mkdocs.yml)
        self._base_dir = [str(v) for v in self._base_dir]

        self._config_path = self.config['config']

        if self.config['config']:
            # try to find config file
            for search_dir in self._base_dir:
                if os.path.isfile(os.path.join(search_dir, self.config['config'])):
                    self._config_path = os.path.join(search_dir, self.config['config'])
                    break
            else:
                logger.error(f'Could not find config file {self._config_path} in any of {self._base_dir}')
                return [self._render_error(f'Could not find config file {self._config_path} in any of {self._base_dir}')]

        text = '\n'.join(lines)
        idx = 0

        # loop until all text is parsed
        while idx < len(text):
            text1, idx1 = self._replace_block(text[idx:])
            text = text[:idx]+text1
            idx += idx1

        return text.split('\n')

    @property
    def _server(self) -> Optional[str]:
        return self._kroki_server or self._plantuml_server

    # regex for removing some parts from the plantuml generated svg
    ADAPT_SVG_REGEX = re.compile(r'^<\?xml .*?\?>')
    # ADAPT_SVG_REGEX = re.compile(r'^<\?xml .*?\?><svg(.*?)xmlns=".*?" (.*?)>')

    def _replace_block(self, text: str) -> Tuple[str, int]:
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
        source = m.group('source') if m.group('source') else None
        self._lang: str = m.group('lang')
        options = {
            'classes': m.group('classes') if m.group('classes') else self.config['classes'],
            'alt': m.group('alt') if m.group('alt') else self.config['alt'],
            'title': m.group('title') if m.group('title') else self.config['title'],
            'width': m.group('width') if m.group('width') else None,
            'height': m.group('height') if m.group('height') else None,
            'id': m.group('id') if m.group('id') else None,
        }

        # Convert image type in PlantUML image format
        if img_format == 'png':
            requested_format = "png"
        elif img_format in ['svg', 'svg_object', 'svg_inline']:
            requested_format = "svg"
        elif img_format == 'txt':
            requested_format = "txt"
        else:
            requested_format = "png"

        # Extract the PlantUML code.
        code = ""
        # Add external diagram source.
        if source and self._base_dir:
            for base_dir in self._base_dir:
                source_path = os.path.join(base_dir, source)

                if os.path.exists(source_path):
                    with open(source_path, 'r', encoding=self._encoding) as f:
                        code += f.read()
                    break
            else:
                diag_tag = self._render_error('Cannot find external diagram source: ' + source)
                return (text[:m.start()] + m.group('indent') + diag_tag + text[m.end():],
                        m.start() + len(m.group('indent')) + len(diag_tag))
        # Add extracted markdown diagram text.
        code += m.group('code')

        # Extract diagram source end convert it
        diagram, err = self._render_diagram(code, requested_format)

        if err:
            # there is an error message: create a nice tag to show it
            diag_tag = self._render_error(err)
        else:
            diag_tag = self._image_tag(img_format, diagram, options, code)

        return text[:m.start()] + m.group('indent') + diag_tag + text[m.end():], \
               m.start() + len(m.group('indent')) + len(diag_tag)

    def _image_tag(self, img_format: str, diagram: bytes, options: Dict[str, Optional[str]], code: str) -> str:
        if img_format == 'txt':
            return self._txt_code(diagram)
        # These are images
        elif img_format == 'svg_inline':
            return self._inline_svg_image(diagram, options)
        elif img_format == 'svg':
            return self._svg_image(diagram, options)
        elif img_format == 'svg_object':
            return self._svg_object_image(diagram, options)
        else:  # png format, explicitly set or as a default when format is not recognized
            return self._png_image(diagram, options, code)

    def _txt_code(self, diagram: bytes) -> str:
        # logger.debug(diagram)
        img = etree.Element('pre')
        code = etree.SubElement(img, 'code')
        code.attrib['class'] = 'text'
        code.text = AtomicString(diagram.decode('UTF-8'))
        return self.md.htmlStash.store(etree.tostring(img, short_empty_elements=True).decode())

    def _inline_svg_image(self, diagram: bytes, options: Dict[str, Optional[str]]) -> str:
        etree.register_namespace("", "http://www.w3.org/2000/svg")
        data = self.ADAPT_SVG_REGEX.sub('', diagram.decode('UTF-8'))
        # data = self.ADAPT_SVG_REGEX.sub('<svg \\1\\2>', diagram.decode('UTF-8'))
        img = etree.fromstring(data.encode('UTF-8'))
        if bool(self.config["remove_inline_svg_size"]):
            # remove width and height in style attribute
            img.attrib['style'] = re.sub(r'\b(?:width|height):\d+px;', '', img.attrib['style'])
        img.attrib['preserveAspectRatio'] = 'xMaxYMax meet'
        self._set_tag_attributes(img, options)

        return self.md.htmlStash.store(etree.tostring(img, short_empty_elements=True).decode())

    def _svg_image(self, diagram: bytes, options: Dict[str, Optional[str]]) -> str:
        # Firefox handles only base64 encoded SVGs
        data = 'data:image/svg+xml;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
        img = etree.Element('img')
        img.attrib['src'] = data
        self._set_tag_attributes(img, options)
        return etree.tostring(img, short_empty_elements=True).decode()

    def _svg_object_image(self, diagram: bytes, options: Dict[str, Optional[str]]) -> str:
        # Firefox handles only base64 encoded SVGs
        data = 'data:image/svg+xml;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
        img = etree.Element('object')
        img.attrib['data'] = data
        self._set_tag_attributes(img, options)
        # object tag must be explicitly closed
        return etree.tostring(img, short_empty_elements=False).decode()

    def _png_image(self, diagram: bytes, options: Dict[str, Optional[str]], code: str) -> str:
        map_tag = ''
        data = 'data:image/png;base64,{0}'.format(base64.b64encode(diagram).decode('ascii'))
        img = etree.Element('img')
        img.attrib['src'] = data

        # check if image maps are enabled
        if str(self.config['image_maps']).lower() in ['true', 'on', 'yes', '1']:
            # Check for hyperlinks
            map_data, err = self._render_diagram(code, 'map')

            if err:
                # there is an error message: create a nice tag to show it
                return self._render_error(err)
            else:
                map_data = map_data.decode("utf-8")

                if map_data.startswith('<map '):
                    # There are hyperlinks, add the image map
                    unique_id = str(uuid.uuid4())
                    map = etree.fromstring(map_data)
                    map.attrib['id'] = unique_id
                    map.attrib['name'] = unique_id
                    map_tag = etree.tostring(map, short_empty_elements=True).decode()
                    img.attrib['usemap'] = '#' + unique_id

        self._set_tag_attributes(img, options)
        diag_tag = etree.tostring(img, short_empty_elements=True).decode()

        return diag_tag + map_tag

    @staticmethod
    def _set_tag_attributes(img, options: Dict[str, Optional[str]]):
        styles = []
        if 'style' in img.attrib and img.attrib['style'] != '':
            styles.append(re.sub(r';$', '', img.attrib['style']))
        if options['width']:
            styles.append("max-width:" + options['width'])
        if options['height']:
            styles.append("max-height:" + options['height'])

        if styles:
            img.attrib['style'] = ";".join(styles)
            img.attrib['width'] = '100%'
            if 'height' in img.attrib:
                img.attrib.pop('height')

        img.attrib['class'] = options['classes']
        img.attrib['alt'] = options['alt']
        img.attrib['title'] = options['title']

        if options['id']:
            img.attrib['id'] = options['id']

    @staticmethod
    def _render_error(msg: str) -> str:
        return f'<div style="color: red">{msg}</div>'

    def _render_diagram(self, code: str, requested_format: str) -> Tuple[Optional[bytes], Optional[str]]:
        cached_diagram_file = None
        diagram = None

        if self._cachedir:
            os.makedirs(self._cachedir, exist_ok=True)
            diagram_hash = "%08x" % (adler32(code.encode('UTF-8')) & 0xffffffff)
            cached_diagram_file = os.path.expanduser(
                    os.path.join(self._cachedir, diagram_hash + '.' + requested_format))

            if os.path.isfile(cached_diagram_file):
                with open(cached_diagram_file, 'rb') as f:
                    diagram = f.read()

        if diagram is not None:
            # if cache found then end this function here
            return diagram, None

        # if cache not found create the diagram
        code = self._set_theme(code)

        if self._server:
            with self._set_session() as session:
                diagram, err = self._render_remote_uml_image(code, requested_format, session)
        else:
            diagram, err = self._render_local_uml_image(code, requested_format)

        if not err and self._cachedir:
            with open(cached_diagram_file, 'wb') as f:
                f.write(diagram)

        return diagram, err

    @staticmethod
    def _set_session() -> Session:
        retries = Retry(
            total=3,
            backoff_factor=1,
            respect_retry_after_header=True,
            status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)

        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

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

    def _render_local_uml_image(self, plantuml_code: str, img_format: str) -> Tuple[Optional[bytes], Optional[str]]:
        plantuml_code = plantuml_code.encode('utf8')
        cmdline = self.config['plantuml_cmd'].split(' ')
        cmdline.extend(['-pipemap' if img_format == 'map' else '-p', "-t" + img_format, '-charset', 'UTF-8'])

        if self._config_path:
            cmdline.extend(['-config', self._config_path])

        try:
            # On Windows run batch files through a shell so the extension can be resolved
            p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=(os.name == 'nt'))
            out, err = p.communicate(input=plantuml_code)
        except Exception as exc:
            raise Exception(f'Failed to run plantuml: {exc}')
        else:
            if p.returncode != 0:
                # plantuml returns a nice image in case of syntax error so log but still return out
                logger.error(f'Error in "uml" directive: {err}')

            return out, None

    def _render_remote_uml_image(
            self, plantuml_code: str, img_format: str, session: requests.Session
        ) -> Tuple[Optional[bytes], Optional[str]]:
        if self._config_path:
            # insert an include directive for the config file as the first statement
            plantuml_code = re.sub(r'^\s*(@start\w+\n)?', r'\1!include '+self._config_path+'\n', plantuml_code)

        # build the whole source diagram, executing include directives
        temp_file = PlantUMLIncluder(self._lang, not not self._kroki_server,
                                     self.config['server_include_whitelist'],
                                     False).readFile(plantuml_code, self._base_dir)
        ssl_verify = not self.config['insecure']

        if not ssl_verify:
            # urllib3 gives a warning is an insecure connection is made, and the warning is included in the output page
            # not the best solution, but it works
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # alternative solution
            # requests.packages.urllib3.disable_warnings()

        # Use GET if preferred, use POST with GET as fallback if POST fails
        if self._http_method == "POST":
            # image_url for POST attempt first
            image_url = "%s/%s/" % (self._server, img_format)
            # download manually the image to be able to continue in case of errors
            r = session.post(image_url, data=temp_file, headers={"Content-Type": 'text/plain; charset=utf-8'},
                             verify=ssl_verify)

            if r.ok:
                return r.content, None

            logger.warning(f'WARNING in "uml" directive: remote server has returned error {r.status_code} on POST')
            if self._fallback_to_get:
                logger.warning('Falling back to GET')
            else:
                return self._handle_response(r)

        if self._kroki_server:
            image_url = self._server + "/plantuml/" + img_format + "/" + self._compress_and_encode(temp_file)
        else:
            image_url = self._server+"/"+img_format+"/"+self._deflate_and_encode(temp_file)

        return self._handle_response(session.get(image_url, verify=ssl_verify))

    def _handle_response(self, resp: Response) -> Tuple[Optional[bytes], Optional[str]]:
        if not resp.ok and self._kroki_server:
            # Kroki sends and HTTP 400 with a text description of the error
            logger.warning(f'WARNING in "uml" directive: remote server has returned error {resp.status_code} on GET: '
                           f'{resp.content.decode("utf-8")}')
            return None, resp.content.decode('utf-8')

        # the response is ok or the server is PlantUML, which sends always a valid image
        return resp.content, None

    @staticmethod
    def _deflate_and_encode(source: str) -> str:
        # algorithm borrowed from the plantuml package
        zlibbed_str = zlib.compress(source.encode('utf-8'))

        return base64.b64encode(zlibbed_str[2:-4]).translate(b64_to_plantuml).decode('utf-8')

    @staticmethod
    def _compress_and_encode(source: str) -> str:
        # diagram encoding for Kroki
        return base64.urlsafe_b64encode(zlib.compress(source.encode('utf-8'), 9)).decode('utf-8')


class PlantUMLIncluder:

    def __init__(self, lang: str, kroki: bool, white_lists: List[str], dark_mode: bool,
                 light_theme: Optional[str] = None, dark_theme: Optional[str] = None):
        self._dark_mode = dark_mode
        self._light_theme = light_theme
        self._dark_theme = dark_theme
        self._definitions: Dict[str, str] = {}
        self._lang = lang
        self._kroki = kroki
        self._white_lists = white_lists
        self._diagram_type = 'uml'

    # Given a PlantUML source, replace any "!include" directive with the included code, recursively
    def readFile(self, plantuml_code: str, directory: List[str]) -> str:
        """
        Reads a PlantUML code and replaces any "!include" directives with the included code, recursively.

        Args:
            plantuml_code (str): The PlantUML code to process.
            directory (List[str]): A list of directories to search for included files.

        Returns:
            str: The processed PlantUML code with all "!include" directives replaced.

        """
        lines = plantuml_code.splitlines()
        # Wrap the whole combined text between startuml and enduml tags as recursive processing would have removed them
        # This is necessary for it to work correctly with plamtuml POST processing
        all_lines = self._readFileRec(lines, directory)
        return "@start"+self._diagram_type+"\n" + "\n".join(all_lines) + "\n@end"+self._diagram_type+"\n"

    # Reads the file recursively
    def _readFileRec(self, lines: List[str], search_dirs: List[str]) -> List[str]:
        """
        Recursively reads a list of lines and replaces any "!include" directives with the included code.

        Args:
            lines (List[str]): The list of lines to process.
            search_dirs (List[str]): A list of directories to search for included files.

        Returns:
            List[str]: The processed list of lines with all "!include" directives replaced.

        """
        result: List[str] = []

        for line in lines:
            line_striped = line.strip()

            # preprocessor, define variable, new syntax
            match = re.search(r'!(?P<varname>\$?\w+)\s+=\s+"(?P<value>.*)"', line_striped)

            if not match:
                # preprocessor, define variable, old syntax
                match = re.search(r'^!define (?P<varname>\w+)\s+(?P<value>.*)', line_striped)

            if match:
                # variable definition, save the mapping as the value can be used in !include directives
                self._definitions[match.group('varname')] = match.group('value')
                result.append(line_striped)
            elif line_striped.startswith("!include"):
                result.append(self._readInclLine(line_striped, search_dirs).strip())
            elif line_striped.startswith("@start"):
                # remove startuml as plantuml POST method doesn't like it in include files
                # we will wrap the whole combined text between start and end tags at the end
                self._diagram_type = line_striped[len("@start"):]  # save the type of plantuml diagram
                continue
            elif line_striped.startswith("@end"):
                # remove startuml and enduml tags as plantuml POST method doesn't like it in include files
                # we will wrap the whole combined text between start and end tags at the end
                continue
            else:
                result.append(line_striped)

        return result

    def _readInclLine(self, line: str, search_dirs: List[str]) -> str:
        """
        Reads the contents of an included file and returns its contents.

        Args:
            line (str): The line containing the !include directive.
            search_dirs (List[str]): A list of directories to search for the included file.

        Returns:
            str: The processed line containing the included file contents, or the original line if the inclusion is
            handled by the server.

        """
        # If includeurl is found, we do not have to do anything here. Server can handle that (if enabled)
        if "!includeurl" in line:
            return line

        # use line comment as a sort of "directive" for hinting that the file will be included by the server
        if re.match(r"[^']+'\s*server.*$", line):  # ex: !include file.puml 'server-side include
            return line  # include handled by server, return it untouched

        # extract the file to include
        line_match = re.match(r"^!include(?:_once|_many)?\s+(?P<filename>[^']+)(?:\s+'(?P<comment>.*))?$", line)
        inc_file = line_match.group('filename')

        # expand variables to be able to detect what kind of file/include is
        for varname, value in self._definitions.items():
            if inc_file.startswith(varname):
                inc_file = inc_file.replace(varname, value)
                break

        if self._dark_mode:
            inc_file = inc_file.replace(self._light_theme, self._dark_theme)

        # According to plantuml, simple !include can also have urls, or use the <> format to include stdlib files,
        # ignore that and continue
        if inc_file.startswith("http") or inc_file.startswith("<"):
            return line  # handled by the server

        # At his point we have a file name/path; it may be handled by the server, or we need to execute the inclusion
        if re.match(r".*'\s*local.*$", line):  # include hint, ex: !include file.puml 'local file
            remote = False
        else:
            # if the filename matches the white list, then it can be included by te server
            remote = any(re.match(r, inc_file) for r in self._white_lists)

        if remote:
            return line  # inclusion handled by the server
        else:
            # Read contents of the included file
            return self._load_file(search_dirs, inc_file)

    def _load_file(self, search_dirs: List[str], inc_file_rel: str):
        """
        Loads a file from a list of search directories.

        Args:
            search_dirs (List[str]): A list of directories to search for the file.
            inc_file_rel (str): The relative path of the file to load.

        Returns:
            str: The contents of the loaded file.

        Raises:
            FileNotFoundError: If the file is not found in any of the search directories.
            Exception: If an error occurs while loading the file.
        """
        for inc_dir in search_dirs:
            inc_file_abs = os.path.normpath(os.path.join(inc_dir, inc_file_rel))
            if os.path.exists(inc_file_abs):
                try:
                    with open(inc_file_abs, "r") as inc:
                        include_dirs = [os.path.dirname(os.path.realpath(inc_file_abs))]
                        include_dirs.extend(search_dirs)
                        return "\n".join(self._readFileRec(inc.readlines(), include_dirs))
                except Exception as exc:
                    logger.error("Could not find include " + str(exc))
                    raise exc
        else:
            raise FileNotFoundError("Could not find include " + inc_file_rel)


# For details see https://python-markdown.github.io/extensions/api/#extendmarkdown
class PlantUMLMarkdownExtension(markdown.Extension):
    # For details see https://python-markdown.github.io/extensions/api/#configsettings
    def __init__(self, **kwargs):
        self.config = {
            'classes': ["uml", "Space separated list of classes for the generated image. Defaults to 'uml'."],
            'alt': ["uml diagram", "Text to show when image is not available. Defaults to 'uml diagram'"],
            'format': ["png", "Format of image to generate (png, svg or txt). Defaults to 'png'."],
            'remove_inline_svg_size': [True, "Remove the width and height attributes of inline_svg diagrams", "Defaults to True"],
            'title': ["", "Tooltip for the diagram"],
            'config': ["", "Path for a PlantUML configuration file (relative to base_dir), included before every "
                           "diagram", "Defaults to blank, no config file"],
            'server': ["", "PlantUML server url, for remote rendering. Defaults to '', use local command."],
            'kroki_server': ["", "Kroki server url, as alternative to 'server' for remote rendering (image maps must "
                                 "be disabled manually). Defaults to '', use PlantUML server if defined"],
            'server_include_whitelist': [[r'^[Cc]4.*$'],
                                         "List of regular expressions defining which include files are supported by "
                                         "the server. Defaults to [r'^c4.*$']"],
            'insecure': [False, "Disable SSL certificates verification; set to True if you server uses self-signed certificates. Defaults to False"],
            'cachedir': ["", "Directory for caching of diagrams. Defaults to '', no caching"],
            'image_maps': ["true", "Enable generation of PNG image maps, allowing to use hyperlinks with PNG images."
                                   "Defaults to true"],
            'priority': ["30", "Extension priority. Higher values means the extension is applied sooner than others. "
                               "Defaults to 30"],
            'base_dir': [".", "Base directory for external files inclusion. Defaults to '.', can be a list of paths."],
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
                                    ],
            "plantuml_cmd": ["plantuml", "Command executed when using local plantuml (ex: 'java -Dplantuml.include.path="
                                         ". -jar plantuml.jar')", "Defaults to 'plantuml'."]
        }

        # Fix to make links navigable in SVG diagrams
        etree.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

        super(PlantUMLMarkdownExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        md.registerExtension(self)
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
