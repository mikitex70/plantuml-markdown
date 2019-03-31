# -*- coding: utf-8 -*-
import os
import re
import unittest
import markdown


class PlantumlTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if cls is PlantumlTest:
            raise unittest.SkipTest("Base class")
        super(PlantumlTest, cls).setUpClass()

    def setUp(self):
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'plantuml-markdown'])
        self.text_builder = None

    def _load_file(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'data', filename), 'r') as f:
            return f.read()[:-1]  # skip the last newline

    FAKE_IMAGE = 'ABCDEF=='
    BASE64_REGEX = re.compile(
        r'("data:image/[a-z+]+;base64,)(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')

    @classmethod
    def _stripImageData(cls, html):
        return cls.BASE64_REGEX.sub(r'\1%s' % cls.FAKE_IMAGE, html)

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

    def test_arg_title(self):
        """
        Test for the correct parsing of the title argument
        """
        text = self.text_builder.diagram("A --> B").title("Diagram test").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="Diagram test" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_title_inline_svg(self):
        """
        Test for setting title attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").title("Diagram test").build()
        self.assertEqual(
            '<p><svg alt="uml diagram" title="Diagram test" class="uml">%s</svg></p>' % self.FAKE_SVG,
            self._stripSvgData(self.md.convert(text)))

    def test_arg_alt(self):
        """
        Test for the correct parsing of the alt argument
        """
        text = self.text_builder.diagram("A --> B").alt("Diagram test").build()
        self.assertEqual(
            '<p><img alt="Diagram test" class="uml" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_alt_inline_svg(self):
        """
        Test for setting alt attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").alt("Diagram test").build()
        self.assertEqual(
            '<p><svg alt="Diagram test" title="" class="uml">%s</svg></p>' % self.FAKE_SVG,
            self._stripSvgData(self.md.convert(text)))

    def test_arg_classes(self):
        """
        Test for the correct parsing of the classes argument
        """
        text = self.text_builder.diagram("A --> B").classes("class1 class2").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="class1 class2" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_classes_inline_svg(self):
        """
        Test for setting class attribute in inline SVG
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").classes("class1 class2").build()
        self.assertEqual(
            '<p><svg alt="uml diagram" title="" class="class1 class2">%s</svg></p>' % self.FAKE_SVG,
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
        self.assertEqual(self._stripImageData(self._load_file('svg_object_diag.html')),
                         self._stripImageData(self.md.convert(text)))

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
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_with_percent(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").width("70%").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:70%%" title="" width="100%%" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_height(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").height("120px").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-height:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_height_percent(self):
        """
        Test for the correct parsing of the width argument
        """
        text = self.text_builder.diagram("A --> B").height("50%").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-height:50%%" title="" width="100%%" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_width_and_height(self):
        """
        Test for the correct parsing of the width and height arguments
        """
        text = self.text_builder.diagram("A --> B").width("120px").height("120px").build()
        self.assertEqual(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" style="max-width:120px;max-height:120px" title="" width="100%%" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_format_width_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").width("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="max-width:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_format_height_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").height("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="max-height:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

    def test_arg_format_width_and_height_svg_inline(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg_inline").width('120px').height("120px").build()
        self.assertEqual(self._stripSvgData('<p><svg alt="uml diagram" title="" class="uml" style="max-width:120px;max-height:120px">...svg-body...</svg></p>'),
                         self._stripSvgData(self.md.convert(text)))

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

    def test_unicode_chars(self):
        """
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
