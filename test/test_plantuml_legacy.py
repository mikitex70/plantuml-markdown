import unittest

from test.markdown_builder import MarkdownBuilder
from test.test_plantuml import PlantumlTest


class PlantumlTest_legacy(PlantumlTest):

    def setUp(self):
        super(PlantumlTest_legacy, self).setUp()
        # Setup testing with old block delimiter (I don't remember where I've seen this syntax)
        self.text_builder = MarkdownBuilder('::uml::')


if __name__ == '__main__':
    unittest.main()
