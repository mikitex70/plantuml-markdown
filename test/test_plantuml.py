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
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'plantuml'])
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

    def test_arg_title(self):
        """
        Test for the correct parsing of the title argument
        """
        text = self.text_builder.diagram("A --> B").title("Diagram test").build()
        self.assertEqual(
            '<p><img alt="uml diagram" classes="uml" src="data:image/png;base64,%s" title="Diagram test" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_alt(self):
        """
        Test for the correct parsing of the alt argument
        """
        text = self.text_builder.diagram("A --> B").alt("Diagram test").build()
        self.assertEqual(
            '<p><img alt="Diagram test" classes="uml" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

    def test_arg_classes(self):
        """
        Test for the correct parsing of the classes argument
        """
        text = self.text_builder.diagram("A --> B").classes("class1 class2").build()
        self.assertEqual(
            '<p><img alt="uml diagram" classes="class1 class2" src="data:image/png;base64,%s" title="" /></p>' % self.FAKE_IMAGE,
            self._stripImageData(self.md.convert(text)))

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

    def test_arg_format_txt(self):
        """
        Test for the correct parsing of the format argument, generating a txt image
        """
        text = self.text_builder.diagram("A --> B").format("txt").build()
        self.assertEqual(self._load_file('txt_diag.html'),
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
