from test.markdown_builder import MarkdownBuilder
from test.test_plantuml import TestPlantuml


class TestPlantumlFenced(TestPlantuml):
    def setup_method(self):
        super(TestPlantumlFenced, self).setup_method()
        # Setup testing with backticks fenced block delimiter
        self.text_builder = MarkdownBuilder()

    def test_tildes(self):
        """
        Test correct parsing with tilde fenced block delimiter
        """
        self.text_builder = MarkdownBuilder("~~~uml")
        text = (
            self.text_builder.text("Paragraph before.\n\n")
            .diagram("A --> B")
            .text("\nParagraph after.")
            .build()
        )
        assert self._stripImageData(
            "<p>Paragraph before.</p>\n"
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="" /></p>\n'
            "<p>Paragraph after.</p>" % self.FAKE_IMAGE
        ) == self._stripImageData(self.md.convert(text))

    def test_plantuml(self):
        """
        Test the support of 'plantuml' language
        """
        text = MarkdownBuilder("```plantuml").diagram("A --> B").build()
        assert self._stripImageData(
            self._load_file("png_diag.html")
        ) == self._stripImageData(self.md.convert(text))

    def test_extended_header(self):
        """
        Test the extended syntax header
        """
        text = (
            self.text_builder.diagram("A --> B")
            .extended_syntax()
            .title("Diagram test")
            .build()
        )
        assert "```{uml" in text  # Check the presence of extended syntax
        assert self._stripImageData(
            '<p><img alt="uml diagram" class="uml" src="data:image/png;base64,%s" title="Diagram test" /></p>'
            % self.FAKE_IMAGE
        ) == self._stripImageData(self.md.convert(text))
