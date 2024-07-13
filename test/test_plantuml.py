# -*- coding: utf-8 -*-
import re
from typing import Union, Callable

import markdown
import tempfile
import mock
import os

from unittest import TestCase, SkipTest
from httpservermock import MethodName, MockHTTPResponse, ServedBaseHTTPServerMock


class PlantumlTest(TestCase):

    @classmethod
    def setUpClass(cls):
        if cls is PlantumlTest:
            raise SkipTest("Base class")
        super(PlantumlTest, cls).setUpClass()

    def setUp(self):
        if markdown.__version__ >= '3.3':
            configs = {
                # fix for fences in Markdown 3.3
                'markdown.extensions.fenced_code': {
                    'lang_prefix': ''
                },
                'markdown.extensions.plantuml_markdown': {
                    'priority': 110
                }
            }
        else:
            configs = {}
            
        if os.environ.get('PLANTUML_SERVER', None):
            configs['plantuml_markdown'] = {
                'server': os.environ.get('PLANTUML_SERVER', None)
            }

        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'admonition', 'pymdownx.snippets',
                                                'plantuml_markdown'],
                                    extension_configs=configs)
        self.text_builder = None

    def _load_file(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'data', filename), 'r') as f:
            return f.read()[:-1]  # skip the last newline

    def _remove_style(self, markup):
        return re.sub(r' style="[^"]*"', '', markup)

    FAKE_IMAGE = 'ABCDEF=='
    IMAGE_REGEX = re.compile(r'<(?:img|.*object)'
                             r'(?:( alt=".*?")|'
                             r'( id=".*?")?|'
                             r'( class=".*?")|'
                             r'( title=".*?")|'
                             r'( style=".*?")|'
                             r'( src=".*?")|'
                             r'( usemap=".*?")|'
                             r'(?:.*?))+(?:/>|></(?:img|.*object>))')
    BASE64_REGEX = re.compile(
        r'("data:image/[a-z+]+;base64,)(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')

    @classmethod
    def _stripImageData(cls, html):
        def sort_attributes(groups):
            elem_id = next(iter(x for x in groups if x and x.startswith(' id=')), '')
            alt = next(x for x in groups if x and x.startswith(' alt='))
            title = next(x for x in groups if x and x.startswith(' title='))
            classes = next(x for x in groups if x and x.startswith(' class='))
            style = next(iter(x for x in groups if x and x.startswith(' style=')), None)
            src = next(iter(x for x in groups if x and x.startswith(' src=')), None)
            usemap = next(iter(x for x in groups if x and x.startswith(' usemap=')), None)
            usemap = ' usemap="test"' if usemap else ''

            style = style if style and '""' not in style else ''
            src = src if src and '""' not in src else ''

            html = "<img{}{}{}{}{}{}/>".format(elem_id, alt, title, classes, style, src, usemap)
            return cls.BASE64_REGEX.sub(r'\1%s' % cls.FAKE_IMAGE, html)

        if html.startswith('<map id='):
            html = html[html.index('<area shape='):]
            html = '<map id="test" name="test">' + html
        return cls.IMAGE_REGEX.sub(lambda x: sort_attributes(x.groups()), html.replace('\n\n', '\n'))

    FAKE_SVG = '...svg-body...'
    SVG_REGEX = re.compile(r'<(?:\w+:)?svg(?:( alt=".*?")|( class=".*?")|( title=".*?")|( style=".*?")|(?:.*?))+>.*</(?:\w+:)?svg>')

    @classmethod
    def _stripSvgData(cls, html):
        """
        Simplifies SVG tags to easy comparing.
        :param html: source HTML
        :return: HTML code with simplified svg tags
        """
        def sort_attributes(groups):
            """
            Sorts attributes in a specific order.
            :param groups: matched attributed groups
            :return: a SVG tag string source
            """
            alt = next(x for x in groups if x.startswith(' alt='))
            title = next(x for x in groups if x.startswith(' title='))
            classes = next(x for x in groups if x.startswith(' class='))
            style = next(iter(x for x in groups if x and x.startswith(' style=')), None)

            style = style if style and '""' not in style else ''

            return "<svg{}{}{}{}>{}</svg>".format(alt, title, classes, style, cls.FAKE_SVG)

        return cls.SVG_REGEX.sub(lambda x: sort_attributes(x.groups()), html)

    def test_priority_after_snippets(self):
        """
        Verifies the normal priority of the plantuml_markdown plugin: it must be executed before the fenced code
        but after the snippets plugin.
        """
        self._test_snippets(30, 'A --> B\n')

    def test_priority_before_snippets(self):
        """
        Verifies changing plugin priority: in must be executed even before the snippets plugin.
        :return:
        """
        # raising priority, so the plantuml plugin is executed before the snippet plugin
        # expecting that the snippet is not inserted in the plantuml source code
        self._test_snippets(40, '--8<-- "test-defs.puml"\n')

    def _test_snippets(self, priority, expected):
        """
        Verifies the execution order with the snippets plugin.
        If priority is lower than 32, the snippets plugin has priority; if greater, the
        plantml_markdown plugin has priority over the snippets plugin.
        :param priority: execution priority of the plantuml_markdown plugin
        :param expected: expected generated plantuml source code
        """
        tempdir = tempfile.gettempdir()
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'pymdownx.snippets', 'plantuml_markdown'],
                                    extension_configs={
                                        'plantuml_markdown': {
                                            'priority': priority
                                        },
                                        'pymdownx.snippets': {
                                            'base_path': [tempdir]  # override default include path
                                        }
                                    })
        defs_filename = 'test-defs.puml'
        defs_file = os.path.join(tempdir, defs_filename)
        # preparing a file to include
        with open(defs_file, 'w') as f:
            f.write('A --> B')

        # from test.markdown_builder import MarkdownBuilder
        from plantuml_markdown.plantuml_markdown import PlantUMLPreprocessor

        # mocking a method to capture the generated PlantUML source code
        with mock.patch.object(PlantUMLPreprocessor, '_render_diagram',
                               return_value=('testing'.encode('utf8'), None)) as mocked_plugin:
            text = self.text_builder.diagram("--8<-- \""+defs_filename+"\"").build()
            self.md.convert(text)
            mocked_plugin.assert_called_with(expected, 'map')

    def test_arg_id(self):
        """
        Test for the correct parsing of the id argument
        """
        text = self.text_builder.diagram("A --> B").id("diag-test").build()
        self.assertEqual(
            self._stripImageData('<p><img id="diag-test" alt="uml diagram" class="uml" src="data:image/png;base64,%s" title=""/></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_title(self):
        """
        Test for the correct parsing of the title argument
        """
        text = self.text_builder.diagram("A --> B").title("Diagram test").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="Diagram test" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_title_characters(self):
        """
        Test for the correct parsing of the title argument with special characters
        """
        text = self.text_builder.diagram("A --> B").title("Diagram-test/%&\"").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="Diagram-test/%%&amp;&quot;" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_title_inline_svg(self):
        """
        Test for setting title attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").title("Diagram test").build()
        self.assertEqual(
            self._stripImageData('<p><svg alt="uml diagram" title="Diagram test" class="uml" style="background:#FFFFFF">%s</svg></p>' % self.FAKE_SVG),
            self._stripSvgData(self.md.convert(text)))

    def test_arg_alt(self):
        """
        Test for the correct parsing of the alt argument
        """
        text = self.text_builder.diagram("A --> B").alt("Diagram test").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="Diagram test" class="uml" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_alt_characters(self):
        """
        Test for the correct parsing of the alt argument with special characters
        """
        text = self.text_builder.diagram("A --> B").alt("Diagram-test/%&\"").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="Diagram-test/%%&amp;&quot;" class="uml" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_alt_inline_svg(self):
        """
        Test for setting alt attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").alt("Diagram test").build()
        self.assertEqual(
            self._stripImageData('<p><svg alt="Diagram test" title="" class="uml" style="background:#FFFFFF">%s</svg></p>' % self.FAKE_SVG),
            self._stripSvgData(self.md.convert(text)))

    def test_arg_classes(self):
        """
        Test for the correct parsing of the classes argument
        """
        text = self.text_builder.diagram("A --> B").classes("class1 class2").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="class1 class2" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_classes_inline_svg(self):
        """
        Test for setting class attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").classes("class1 class2").build()
        self.assertEqual(
            self._stripImageData('<p><svg alt="uml diagram" title="" class="class1 class2" style="background:#FFFFFF">%s</svg></p>' % self.FAKE_SVG),
            self._stripSvgData(self.md.convert(text)))

    def test_arg_format_png(self):
        """
        Test for the correct parsing of the format argument, generating a png image
        """
        text = self.text_builder.diagram("A --> B").format("png").build()
        self.assertEqual(self._stripImageData(self._load_file('png_diag.html')),
                         self._stripImageData(self.md.convert(text)))

    def test_arg_format_svg(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg").build()
        self.assertEqual(self._stripImageData(self._load_file('svg_diag.html')),
                         self._stripImageData(self.md.convert(text)))

    def test_arg_format_svg_object(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_object").build()
        html = self.md.convert(text)

        if markdown.__version__ >= '3.3':
            expected = 'svg_object_diag-3.3.html'
        else:
            expected = 'svg_object_diag.html'

        self.assertEqual(self._stripImageData(self._load_file(expected)),
                         self._stripImageData(html))
        # verify that the tag is explicitly closed
        self.assertIsNotNone(re.match(r'.*<object .*?></object>.*', html))

    def test_arg_format_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").build()
        self.assertEqual(self._stripSvgData(self._load_file('svg_inline_diag.html')),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_format_txt(self):
        """
        Test for the correct parsing of the format argument, generating a txt image
        """
        text = self.text_builder.diagram("A --> B").format("txt").build()
        self.assertEqual(self._load_file('txt_diag.html'),
                         self.md.convert(text))

    def test_arg_width(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").width("120px").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_with_percent(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").width("70%").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:70%%" title="" width="100%%" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_height(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").height("120px").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-height:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_height_percent(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").height("50%").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-height:50%%" title="" width="100%%" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_width_and_height(self):
        """
        Test for the correct parsing of the width and height arguments
        """
        text = self.text_builder.diagram("A --> B").width("120px").height("120px").build()
        self.assertEqual(
            self._stripImageData('<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:120px;max-height:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE),
            self._stripImageData(self.md.convert(text)))

    def test_arg_format_width_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").width("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="background:#FFFFFF;max-width:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_format_height_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").height("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="background:#FFFFFF;max-height:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_format_width_and_height_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").width('120px').height("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="background:#FFFFFF;max-width:120px;max-height:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_source(self):
        """
        Test for the correct parsing of the source argument
        """
        include_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        configs = {
            'plantuml_markdown': {
                'base_dir': include_path
            }
        }
            
        if os.environ.get('PLANTUML_SERVER', None):
            configs['plantuml_markdown']['server'] = os.environ.get('PLANTUML_SERVER', None)

        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'pymdownx.snippets', 'plantuml_markdown'],
                                    extension_configs=configs)

        text = self.text_builder.diagram("B -> C")\
                        .source("included_diag.puml")\
                        .format("txt")\
                        .build()
        # ensure that the inline source diagram is appended to the external source
        self.assertEqual(self._load_file('include_output.html'),
                         self.md.convert(text))

    COORDS_REGEX = re.compile(r' coords="\d+(?:,\d+)+"')
    UUID_REGEX = re.compile(r'"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"')

    def test_plantuml_map(self):
        """
        Test map markup is generated for plantuml with links
        """
        text = self.text_builder.diagram('A --> B [[https://www.google.fr]]').build()
        self.assertEqual(
            self._stripImageData("""<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="" usemap="test" /><map id="test" name="test">
<area shape="rect" id="id1" href="https://www.google.fr" title="https://www.google.fr" alt="" coords="1,2,3,4" />
</map></p>""" % self.FAKE_IMAGE),
            self.UUID_REGEX.sub('"test"', self.COORDS_REGEX.sub(' coords="1,2,3,4"', self._stripImageData(self.md.convert(text)))))

    def test_plantuml_map_disabled(self):
        """
        Test map markup is not generated when disabled
        """
        include_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        configs = {
            'plantuml_markdown': {
                'base_dir': include_path,
                'image_maps': 'false'
            }
        }
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'pymdownx.snippets', 'plantuml_markdown'],
                                    extension_configs=configs)

        text = self.text_builder.diagram('A --> B [[https://www.google.fr]]').build()
        result = self._stripImageData(self.md.convert(text))
        self.assertFalse("<map " in result)

    def test_multidiagram(self):
        """
        Test for the definition of multiple diagrams on the same document
-       """
        text = self.text_builder.text('Paragraph before.\n\n') \
            .diagram('A --> B') \
            .text('\nMiddle paragraph.\n\n') \
            .diagram('A <- B') \
            .text('\nParagraph after.\n\n') \
            .build()
        self.assertEqual(self._stripImageData(self._load_file('multiple_diag.html')),
                         self._stripImageData(self.md.convert(text)))

    def test_other_fenced_code(self):
        """
        Test the coexistence of diagrams and other fenced code
        """
        text = self.text_builder.text('```bash\nls -l\n```\n') \
            .text('\nA paragraph\n\n') \
            .diagram('A --> B') \
            .text('\nAnother paragraph\n') \
            .build()
        self.assertEqual(self._stripImageData(self._load_file('code_and_diag.html')),
                         self._stripImageData(self.md.convert(text)))

    def test_diagram_in_fenced_code(self):
        """
        Diagrams inside fenced code must not be touched
        """
        text = self.text_builder.text('````markdown\n') \
            .text('```uml\n') \
            .text('A --> B\n') \
            .text('```\n') \
            .text('````\n') \
            .build()
        self.assertEqual('''<pre><code class="markdown">```uml
A --&gt; B
```
</code></pre>''', self.md.convert(text))

    def test_indented_fenced_code(self):
        """
        Test handling of indented fenced code
        """
        text = self.text_builder.text('* list item\n\n') \
            .indent(4) \
            .diagram('A --> B') \
            .build()
        self.assertEqual(self._stripImageData('''<ul>
<li>
<p>list item</p>
<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="" /></p>
</li>
</ul>''' % self.FAKE_IMAGE),
                          self._stripImageData(self.md.convert(text)))

    def test_multiple_fences(self):
        """
        Test multiple fences in document.
        Single document with a mix of fence code and plantuml diagrams.
        """
        text = self.text_builder.text('````markdown\n') \
            .text('    ```uml\n') \
            .text('    A --> B\n') \
            .text('    ```\n') \
            .text('````\n') \
            .diagram('A --> B') \
            .text('````markdown\n') \
            .text('    ```uml\n') \
            .text('    A <-- B\n') \
            .text('    ```\n') \
            .text('````\n') \
            .diagram('A <-- B') \
            .build()
        self.assertEqual('''<pre><code class="markdown">    ```uml
    A --&gt; B
    ```
</code></pre>
<p><img alt="uml diagram" title="" class="uml" src="data:image/png;base64,%s"/></p>
<pre><code class="markdown">    ```uml
    A &lt;-- B
    ```
</code></pre>
<p><img alt="uml diagram" title="" class="uml" src="data:image/png;base64,%s"/></p>''' %
                         (self.FAKE_IMAGE, self.FAKE_IMAGE), self._stripImageData(self.md.convert(text)))

    def test_admonition(self):
        text = self.text_builder.text('!!! note\n') \
            .indent(4) \
            .diagram('A --> B') \
            .build()
        self.assertEqual('''<div class="admonition note">
<p class="admonition-title">Note</p>
<p><img alt="uml diagram" title="" class="uml" src="data:image/png;base64,%s"/></p>
</div>''' % self.FAKE_IMAGE, self._stripImageData(self.md.convert(text)))

    def test_unicode_chars(self):
        """indented_code
        Test that svg_inline handles correctly utf8 characters
        """
        # Example diagram from issue 21
        text = self.text_builder.diagram(u'Alicja -> Łukasz: "Zażółć gęślą jaźń"')\
            .format("svg_inline")\
            .build()
        svg = self.md.convert(text)
        self.assertTrue('Alicja' in svg)
        self.assertTrue('&#321;ukasz' in svg)
        self.assertTrue('"Za&#380;&#243;&#322;&#263; g&#281;&#347;l&#261; ja&#378;&#324;"' in svg)

    def test_json(self):
        """
        Test that we can use startjson and similar tags to change diagram kind
        """
        text = self.text_builder.diagram('''
        @startjson
        {
           "fruit":"Apple",
           "size":"Large",
           "color":"Red"
        }
        @endjson
        ''').format("txt").build()
        self.assertEqual('''<pre><code class="text">                                                                                                      
                                                                                                      
               fruit                                                                             Apple
                                                                                                      
               size                                                                              Large
                                                                                                      
               color                                                                             Red  
</code></pre>''', self.md.convert(text))

#     def test_yaml(self):
#         """
#         Verify that spaces are not removed
#         """
#         text = self.text_builder.diagram('''
# @startyaml
# fruit: Apple
# size: Large
# color:
#   background: Red
#   foreground: Green
#   other:
#     data1: 1
#     data2:
#       - x
#       - y
# @endyaml
#         ''').format("png").build()
#         generated = self.md.convert(text)
#
#         with open('/tmp/test.html', 'w') as f:
#             f.write(generated)
#
#         self.assertEqual(self._load_file('yaml_diagram.html'), generated)

    def test_source(self):
        include_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        configs = {
            'plantuml_markdown': {
                'base_dir': include_path,
                'encoding': 'cp1252'
            }
        }
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'pymdownx.snippets', 'plantuml_markdown'],
                                    extension_configs=configs)

        text = self.text_builder.diagram(" ")\
            .source("included_source.puml")\
            .format("txt")\
            .build()
        self.assertRegex(self.md.convert(text),
                         re.compile(r'<pre><code class=\"text\">\s+,-+\.\s+,-\.\n'
                                    r'\s+\|.*\|\s+\|A\|'
                                    r'.*'
                                    r'\s+\|.*\|\s+'
                                    r'\s+\|\s*&lt;-+\|\s+'
                                    r'\s+,-+.*,\+\.'
                                    r'\s+\|.*\|\s+\|A\|'
                                    r"\s+`-+'\s+`-'\n"
                                    r'</code></pre>', re.DOTALL))

    def _server_render(self, filename: str, text: Union[str, Callable[[str], str]],
                       expected='<pre><code class="text">A -&gt; B -&gt; C</code></pre>',
                       server='server'):
        """
        Support method for simulating server rendering and keep tests simple.
        :param filename: filename with diagram source to include
        :param text: Markdown text, or lambda generating it
        :param expected: expected HTML result
        :param server: key for the server url to configure, `server` or `kroki_server`
        """
        tempdir = tempfile.gettempdir()
        defs_file = os.path.join(tempdir, filename)
        # preparing a file to include
        with open(defs_file, 'w') as f:
            f.write('A --> B')

            with ServedBaseHTTPServerMock() as server_mock:
                server_mock.responses[MethodName.GET].append(
                    MockHTTPResponse(status_code=200, headers={}, reason_phrase='', body=b"A -> B -> C")
                )
                if callable(text):
                    text = self.text_builder.diagram(text(server_mock.url)).format('txt').build()
                else:
                    text = self.text_builder.diagram(text).format('txt').build()

                self.md = markdown.Markdown(extensions=['plantuml_markdown'],
                                            extension_configs={
                                                'plantuml_markdown': {
                                                    server: server_mock.url,
                                                    'base_dir': tempdir
                                                }
                                            })
                self.assertEqual(expected, self.md.convert(text))

    def test_include_local(self):
        """
        Test inclusion of local files.
        """
        self._server_render('local-file.puml', f"""
@startuml
!include local-file.puml

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """)

    def test_include_local_forced(self):
        """
        Test inclusion of local files with a "hint" to force loading locally.
        Otherwise, the c4_context.puml file would be included by the server.
        """
        self._server_render('c4_context.puml', f"""
@startuml
!include c4_context.puml 'local file

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """)

    def test_include_server_forced(self):
        """
        Test inclusion of a server side file, with a "hint" to force it.
        Otherwise, the file will be searched locally.
        """
        self._server_render('unused.puml', f"""
@startuml
!include my_server_include.puml 'server-side inclusion

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """)

    def test_include_server_plantuml(self):
        """
        Test inclusion of auto-detected remote files when using a Kroki server.
        """
        self._server_render('c4_context.puml', f"""
@startuml
' This includes must be automatically supported by the server
!include c4_component.puml
!include c4_container.puml
!include c4_context.puml
!include c4_deployment.puml
!include c4_dynamic.puml
!include c4.puml

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """)

    def test_include_server_kroki_automatic(self):
        """
        Test inclusion of auto-detected remote files when using a Kroki server.
        """
        self._server_render('c4_context.puml', f"""
@startuml
' This includes must be automatically supported by the server
!include c4_component.puml
!include c4_container.puml
!include c4_context.puml
!include c4_deployment.puml
!include c4_dynamic.puml
!include c4.puml

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """, server='kroki_server')

    def test_include_server(self):
        """
        Test inclusion of server-side files.
        """
        self._server_render('unused.puml', f"""
@startuml
' This includes must be automatically supported by the server
!includeurl 'some-url'
!include http://some-server
!include https://some-server
!include_once http://some-server
!include_many http://some-server
!include <stdlib/file>

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """)

    def test_include_with_variables(self):
        """
        Test inclusion of local files, with the use variables for substitutions.
        :return:
        """
        self._server_render('local-file.puml', lambda server_url: f"""
@startuml
!define myserver {server_url}
!$my_other_server = "{server_url}"
!include myserver/first_include.puml
!include $my_other_server/second_include.puml
'!include local-file.puml

dummy   'the plantuml response is mocked, any text is good
@enduml        
        """, '<pre><code class="text">A -&gt; B -&gt; C</code></pre>')

    def test_kroki(self):
        """
        Test calling a kroki server for rendering
        """
        with ServedBaseHTTPServerMock() as kroki_server_mock:
            kroki_server_mock.responses[MethodName.GET].append(
                MockHTTPResponse(status_code=200, headers={}, reason_phrase='', body=b"dummy")
            )
            self.md = markdown.Markdown(extensions=['plantuml_markdown'],
                                        extension_configs={
                                            'plantuml_markdown': {
                                                'kroki_server': kroki_server_mock.url,
                                                'image_maps': 'no'
                                            }
                                        })
            text = self.text_builder.diagram('A -> B').format('png').build()

            self.assertEqual(self._stripImageData(self._load_file('png_diag.html')),
                             self._stripImageData(self.md.convert(text)))
            req = kroki_server_mock.requests[MethodName.GET].pop(0)
            self.assertTrue(req.path.startswith('/plantuml/png/'))

    def test_retries(self):
        """
        Test retrying on 429 responses
        """
        with ServedBaseHTTPServerMock() as plantumlserver_mock:
            plantumlserver_mock.responses[MethodName.GET].append(
                MockHTTPResponse(
                    status_code=429,
                    headers={"Retry-After": "1"},
                    reason_phrase='Too many requests',
                    body=b"")
            )
            plantumlserver_mock.responses[MethodName.GET].append(
                MockHTTPResponse(status_code=200, headers={}, reason_phrase='', body=b"dummy")
            )
            self.md = markdown.Markdown(extensions=['plantuml_markdown'],
                                        extension_configs={
                                            'plantuml_markdown': {
                                                'server': plantumlserver_mock.url,
                                            }
                                        })
            text = self.text_builder.diagram('A -> B').format('txt').build()
            self.assertEqual('<pre><code class="text">dummy</code></pre>',
                             self.md.convert(text))

    def test_cachedir(self):
        """
        Verify that `cachedir` is created if it does not exist
        """
        temp_dir = tempfile.TemporaryDirectory()
        cache_dir = os.path.join(temp_dir.name, 'cache', 'dir')
        self.md = markdown.Markdown(extensions=['plantuml_markdown'],
                                    extension_configs={
                                        'plantuml_markdown': {
                                            'cachedir': cache_dir,
                                        }
                                    })
        text = self.text_builder.diagram("A --> B").build()
        self.md.convert(text)
        self.assertTrue(os.path.exists(cache_dir))
        temp_dir.cleanup()
