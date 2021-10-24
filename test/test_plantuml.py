# -*- coding: utf-8 -*-
import os
import re
import sys

import markdown
import tempfile
from unittest import TestCase, SkipTest
import mock
import os


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
                             r'( class=".*?")|'
                             r'( title=".*?")|'
                             r'( style=".*?")|'
                             r'( src=".*?")|'
                             r'(?:.*?))+(?:/>|></(?:img|.*object>))')
    BASE64_REGEX = re.compile(
        r'("data:image/[a-z+]+;base64,)(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')

    @classmethod
    def _stripImageData(cls, html):
        def sort_attributes(groups):
            alt = next(x for x in groups if x.startswith(' alt='))
            title = next(x for x in groups if x.startswith(' title='))
            classes = next(x for x in groups if x.startswith(' class='))
            style = next(iter(x for x in groups if x and x.startswith(' style=')), None)
            src = next(iter(x for x in groups if x and x.startswith(' src=')), None)

            style = style if style and '""' not in style else ''
            src = src if src and '""' not in src else ''

            html = "<img{}{}{}{}{}/>".format(alt, title, classes, style, src)
            return cls.BASE64_REGEX.sub(r'\1%s' % cls.FAKE_IMAGE, html)

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
        Verifies the normal priority of the plantuml_markdown plugin: it must be execute before the fenced code
        but after the snippets plugin.
        """
        self._test_snippets(30, 'A --> B\n')

    def test_priority_before_snippets(self):
        """
        Verifies changing plugin priority: in must be execute even before the snippets plugin.
        :return:
        """
        # raising priority, so the plantuml plugin is executed before the snippet plugin
        # expecting that the snippet is not inserted in the plantuml source code
        self._test_snippets(40, '--8<-- "'+os.path.join(tempfile.gettempdir(), 'test-defs.puml')+'"\n')

    def _test_snippets(self, priority, expected):
        """
        Verifies the execution order with the snippets plugin.
        If priority is lower than 32, the snippets plugin has priority; if greater, the
        plantml_markdown plugin has priority over the snippets plugin.
        :param priority: execution priority of the plantuml_markdown plugin
        :param expected: expected generated plantuml source code
        """
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code',
                                                'pymdownx.snippets', 'plantuml_markdown'],
                                    extension_configs={
                                        'plantuml_markdown': {
                                            'priority': priority
                                        }
                                    })
        tempdir = tempfile.gettempdir()
        defs_file = os.path.join(tempdir, 'test-defs.puml')
        # preparing a file to include
        with open(defs_file, 'w') as f:
            f.write('A --> B')

        from test.markdown_builder import MarkdownBuilder
        from plantuml_markdown import PlantUMLPreprocessor

        # mcking a method to capture the generated PlantUML source code
        with mock.patch.object(PlantUMLPreprocessor, '_render_diagram',
                            return_value='testing'.encode('utf8')) as mocked_plugin:
            text = self.text_builder.diagram("--8<-- \"" + defs_file + "\"").build()
            self.md.convert(text)
            mocked_plugin.assert_called_with(expected, 'png')

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
               fruit          Apple
               size           Large
                                   
               color          Red  
</code></pre>''', self.md.convert(text))

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
        self.assertEqual('''<pre><code class="text">     ,------.          ,-.
     |&#192;&#210;&#200;&#201;&#204;&#217;|          |A|
     `--+---'          `+'
        |   "&#242;&#224;&#232;&#236;&#233;&#249;"    | 
        | &lt;-------------| 
     ,--+---.          ,+.
     |&#192;&#210;&#200;&#201;&#204;&#217;|          |A|
     `------'          `-'
</code></pre>''', self.md.convert(text))
