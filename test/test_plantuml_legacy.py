from test.markdown_builder import MarkdownBuilder
from test.test_plantuml import TestPlantuml


class TestPlantumlLegacy(TestPlantuml):
    def setup_method(self):
        super(TestPlantumlLegacy, self).setup_method()
        # Setup testing with old block delimiter (I don't remember where I've seen this syntax)
        self.text_builder = MarkdownBuilder("::uml::")

    def test_multiple_fences(self):
        pass  # this test has no sense with legacy diagram delimiter
