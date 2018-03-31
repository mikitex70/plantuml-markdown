import os
import unittest
import markdown

class PlantumlTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if cls is PlantumlTest:
            raise unittest.SkipTest("Base class")
        super().setUpClass()

    def setUp(self):
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'plantuml'])
        self.text_builder = None

    def _load_file(self, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'data', filename), 'r') as f:
            return f.read()[:-1]  # skip the las newline

    def test_arg_title(self):
        """
        Test for the correct parsing of the title argument
        """
        text = self.text_builder.diagram("A --> B").title("Diagram test").build()
        self.assertEqual(
            '<p><img alt="uml diagram" classes="uml" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE8AAABwCAIAAADQerqpAAAANXRFWHRjb3B5bGVmdABHZW5lcmF0ZWQgYnkgaHR0cDovL3BsYW50dW1sLnNvdXJjZWZvcmdlLm5ldDpnVRsAAAC5elRYdHBsYW50dW1sAAB4nB2NywrCMBQF94H+w1m2i0pStT4W4oOiSAti1a2kNouAvZH0pvj5SrdnZjjbnrXn0L0jsUOabrCPRCS2htpxE5e3Jr5XJQbje+sISzmdxbVmnDVBrqDUWi7W8xUOxQ2ZVHki4uOlRO+Cfxm0tmdvm8D/NhFnPej4ViWoC1wDse0MChqsd9QZ4pHj5Lj+OB69fJbuLaM2/v+PRyXUZDmRT5VnaaMyUVoK3x+7CDnw3p6twQAABChJREFUeNrtm19IU1Ecx2+arTWMIB+kSER7CYUiIcvM8imKQhYRJmIhgx58FhUkjdCI5rKHwBq1TWO5ubg5EkdyUzBHW9nAoMagRpamLnH+ycYS7ac3wvyzO3fvzm3b78d5uAzO/Z7P+b97zpdaiKWgkHbBPzE12t0vSPJ7pzkLQUxubVrI1kodEiSN9fRz0hKTC0TrvK0c7W4NOTlVyg3REpALRAuvmJ9/G3IaedG6IVoCcmGntajUVqvV4XC4XK6hoaHJyUkR5cJOa6xtMJvNDMPY7XYogcfjEVEu7LQtVfV6vZ6maSgBVDnUt4hyYadtrqzTarVQAqhy6GNut1tEubDTGmqUIK/T6YxGI9Q39C4R5ZAWaVcktfoqRVGNjeXhpk1K2kEtRXx8XGKiTKGQj4/3kKbNzT1QWHgyK2sfAVqd7jr77HZ3ZGSkl5VdIErrcrUnJGyGOpZKJQMDRmK0kEpLC+TyfKK01dUKVrKk5Ex5+SVitE4nnZq6S6O5RpQ2JSXZYLgJDxbL3eTknWTGLRvFxadnZ1+Ro2WYezKZ1O9/Dc9zc2+gNMBMpm293l7oyTk5+8nRQu+l/o2iolPExu3U1EtQ7O19SIJ2ZsYK81Nfn/bvLzZbC/wChSBJC/2LBC0sszBoV/yYlra7qamaAC3UNay3UAAYQSRoYZmtqLi8eopecywJPktJJFsKCk7A+oc7R6RFWqRFWqRFWqSNAFqnSgmvCDmxBzPB0xKQC/sZX/C0BOTWOb/1To/19LPJolIbaxtaquqbK+vgXRtOmmZOWmJy3GfzVqvVbDbr9Xotjwh8VkBMjpvW4XBAJdE0Da/QhRSc50DE5LhpoTPY7XbIDLVlDCk4z/iIyXHTQvVANqgn6BjMqtBcqWK4gvP8lpgcNy1kgBqCnDAGXKviTsJBF1dARsgOL4FX+Xw+EeX43iCCSZ/kFSCeckiLtOvFu5r7JGl5yuHNP6RF2tijja1ZSpAV6MeX0Y/qpz+/fY+V9Xa407p4b09ydNDIxMTu4vPj5+z3B5PsuE1R5/NMRPleaqTLZkrMN0mPLWLHZXdmFq5o6mjbS7HAT7bn//nOtCl7eVOLPEuBPJSJLYRQz12HS5d/WDNty2MfBtuYaFtvv9LdhvgjLF7H3nPmPWefpcvf39CuOYwjm5ZFbZPmdWZehP7cd74SOvb8r7ko3Et9etDONqmAjfmfzlLsetu2NTdwY0bJXurDrUcz7mH8doG0SIv/+PDfPNIiLdLid6lIW4GCN7Iv3fwh55vnKYe+efTNo28effPom0ffvDhyeGMXadE3j7559M2jbz4UWvTNo28effOh0KJvHn3z6JvHfTLSIi3SIi3SIi3Som8effPom0ffPPrmycrx9c0HEwL65nnK8fXNBxMC+uZ5yuHtMKRF2siL3/yLy5JOUvXZAAAAAElFTkSuQmCC" title="Diagram test" /></p>',
            self.md.convert(text))

    def test_arg_alt(self):
        """
        Test for the correct parsing of the alt argument
        """
        text = self.text_builder.diagram("A --> B").alt("Diagram test").build()
        self.assertEqual(
            '<p><img alt="Diagram test" classes="uml" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE8AAABwCAIAAADQerqpAAAANXRFWHRjb3B5bGVmdABHZW5lcmF0ZWQgYnkgaHR0cDovL3BsYW50dW1sLnNvdXJjZWZvcmdlLm5ldDpnVRsAAAC5elRYdHBsYW50dW1sAAB4nB2NywrCMBQF94H+w1m2i0pStT4W4oOiSAti1a2kNouAvZH0pvj5SrdnZjjbnrXn0L0jsUOabrCPRCS2htpxE5e3Jr5XJQbje+sISzmdxbVmnDVBrqDUWi7W8xUOxQ2ZVHki4uOlRO+Cfxm0tmdvm8D/NhFnPej4ViWoC1wDse0MChqsd9QZ4pHj5Lj+OB69fJbuLaM2/v+PRyXUZDmRT5VnaaMyUVoK3x+7CDnw3p6twQAABChJREFUeNrtm19IU1Ecx2+arTWMIB+kSER7CYUiIcvM8imKQhYRJmIhgx58FhUkjdCI5rKHwBq1TWO5ubg5EkdyUzBHW9nAoMagRpamLnH+ycYS7ac3wvyzO3fvzm3b78d5uAzO/Z7P+b97zpdaiKWgkHbBPzE12t0vSPJ7pzkLQUxubVrI1kodEiSN9fRz0hKTC0TrvK0c7W4NOTlVyg3REpALRAuvmJ9/G3IaedG6IVoCcmGntajUVqvV4XC4XK6hoaHJyUkR5cJOa6xtMJvNDMPY7XYogcfjEVEu7LQtVfV6vZ6maSgBVDnUt4hyYadtrqzTarVQAqhy6GNut1tEubDTGmqUIK/T6YxGI9Q39C4R5ZAWaVcktfoqRVGNjeXhpk1K2kEtRXx8XGKiTKGQj4/3kKbNzT1QWHgyK2sfAVqd7jr77HZ3ZGSkl5VdIErrcrUnJGyGOpZKJQMDRmK0kEpLC+TyfKK01dUKVrKk5Ex5+SVitE4nnZq6S6O5RpQ2JSXZYLgJDxbL3eTknWTGLRvFxadnZ1+Ro2WYezKZ1O9/Dc9zc2+gNMBMpm293l7oyTk5+8nRQu+l/o2iolPExu3U1EtQ7O19SIJ2ZsYK81Nfn/bvLzZbC/wChSBJC/2LBC0sszBoV/yYlra7qamaAC3UNay3UAAYQSRoYZmtqLi8eopecywJPktJJFsKCk7A+oc7R6RFWqRFWqRFWqSNAFqnSgmvCDmxBzPB0xKQC/sZX/C0BOTWOb/1To/19LPJolIbaxtaquqbK+vgXRtOmmZOWmJy3GfzVqvVbDbr9Xotjwh8VkBMjpvW4XBAJdE0Da/QhRSc50DE5LhpoTPY7XbIDLVlDCk4z/iIyXHTQvVANqgn6BjMqtBcqWK4gvP8lpgcNy1kgBqCnDAGXKviTsJBF1dARsgOL4FX+Xw+EeX43iCCSZ/kFSCeckiLtOvFu5r7JGl5yuHNP6RF2tijja1ZSpAV6MeX0Y/qpz+/fY+V9Xa407p4b09ydNDIxMTu4vPj5+z3B5PsuE1R5/NMRPleaqTLZkrMN0mPLWLHZXdmFq5o6mjbS7HAT7bn//nOtCl7eVOLPEuBPJSJLYRQz12HS5d/WDNty2MfBtuYaFtvv9LdhvgjLF7H3nPmPWefpcvf39CuOYwjm5ZFbZPmdWZehP7cd74SOvb8r7ko3Et9etDONqmAjfmfzlLsetu2NTdwY0bJXurDrUcz7mH8doG0SIv/+PDfPNIiLdLid6lIW4GCN7Iv3fwh55vnKYe+efTNo28effPom0ffvDhyeGMXadE3j7559M2jbz4UWvTNo28effOh0KJvHn3z6JvHfTLSIi3SIi3SIi3Som8effPom0ffPPrmycrx9c0HEwL65nnK8fXNBxMC+uZ5yuHtMKRF2siL3/yLy5JOUvXZAAAAAElFTkSuQmCC" title="" /></p>',
            self.md.convert(text))

    def test_arg_classes(self):
        """
        Test for the correct parsing of the classes argument
        """
        text = self.text_builder.diagram("A --> B").classes("class1 class2").build()
        self.assertEqual(
            '<p><img alt="uml diagram" classes="class1 class2" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE8AAABwCAIAAADQerqpAAAANXRFWHRjb3B5bGVmdABHZW5lcmF0ZWQgYnkgaHR0cDovL3BsYW50dW1sLnNvdXJjZWZvcmdlLm5ldDpnVRsAAAC5elRYdHBsYW50dW1sAAB4nB2NywrCMBQF94H+w1m2i0pStT4W4oOiSAti1a2kNouAvZH0pvj5SrdnZjjbnrXn0L0jsUOabrCPRCS2htpxE5e3Jr5XJQbje+sISzmdxbVmnDVBrqDUWi7W8xUOxQ2ZVHki4uOlRO+Cfxm0tmdvm8D/NhFnPej4ViWoC1wDse0MChqsd9QZ4pHj5Lj+OB69fJbuLaM2/v+PRyXUZDmRT5VnaaMyUVoK3x+7CDnw3p6twQAABChJREFUeNrtm19IU1Ecx2+arTWMIB+kSER7CYUiIcvM8imKQhYRJmIhgx58FhUkjdCI5rKHwBq1TWO5ubg5EkdyUzBHW9nAoMagRpamLnH+ycYS7ac3wvyzO3fvzm3b78d5uAzO/Z7P+b97zpdaiKWgkHbBPzE12t0vSPJ7pzkLQUxubVrI1kodEiSN9fRz0hKTC0TrvK0c7W4NOTlVyg3REpALRAuvmJ9/G3IaedG6IVoCcmGntajUVqvV4XC4XK6hoaHJyUkR5cJOa6xtMJvNDMPY7XYogcfjEVEu7LQtVfV6vZ6maSgBVDnUt4hyYadtrqzTarVQAqhy6GNut1tEubDTGmqUIK/T6YxGI9Q39C4R5ZAWaVcktfoqRVGNjeXhpk1K2kEtRXx8XGKiTKGQj4/3kKbNzT1QWHgyK2sfAVqd7jr77HZ3ZGSkl5VdIErrcrUnJGyGOpZKJQMDRmK0kEpLC+TyfKK01dUKVrKk5Ex5+SVitE4nnZq6S6O5RpQ2JSXZYLgJDxbL3eTknWTGLRvFxadnZ1+Ro2WYezKZ1O9/Dc9zc2+gNMBMpm293l7oyTk5+8nRQu+l/o2iolPExu3U1EtQ7O19SIJ2ZsYK81Nfn/bvLzZbC/wChSBJC/2LBC0sszBoV/yYlra7qamaAC3UNay3UAAYQSRoYZmtqLi8eopecywJPktJJFsKCk7A+oc7R6RFWqRFWqRFWqSNAFqnSgmvCDmxBzPB0xKQC/sZX/C0BOTWOb/1To/19LPJolIbaxtaquqbK+vgXRtOmmZOWmJy3GfzVqvVbDbr9Xotjwh8VkBMjpvW4XBAJdE0Da/QhRSc50DE5LhpoTPY7XbIDLVlDCk4z/iIyXHTQvVANqgn6BjMqtBcqWK4gvP8lpgcNy1kgBqCnDAGXKviTsJBF1dARsgOL4FX+Xw+EeX43iCCSZ/kFSCeckiLtOvFu5r7JGl5yuHNP6RF2tijja1ZSpAV6MeX0Y/qpz+/fY+V9Xa407p4b09ydNDIxMTu4vPj5+z3B5PsuE1R5/NMRPleaqTLZkrMN0mPLWLHZXdmFq5o6mjbS7HAT7bn//nOtCl7eVOLPEuBPJSJLYRQz12HS5d/WDNty2MfBtuYaFtvv9LdhvgjLF7H3nPmPWefpcvf39CuOYwjm5ZFbZPmdWZehP7cd74SOvb8r7ko3Et9etDONqmAjfmfzlLsetu2NTdwY0bJXurDrUcz7mH8doG0SIv/+PDfPNIiLdLid6lIW4GCN7Iv3fwh55vnKYe+efTNo28effPom0ffvDhyeGMXadE3j7559M2jbz4UWvTNo28effOh0KJvHn3z6JvHfTLSIi3SIi3SIi3Som8effPom0ffPPrmycrx9c0HEwL65nnK8fXNBxMC+uZ5yuHtMKRF2siL3/yLy5JOUvXZAAAAAElFTkSuQmCC" title="" /></p>',
            self.md.convert(text))

    def test_arg_format_png(self):
        """
        Test for the correct parsing of the format argument, generating a png image
        """
        text = self.text_builder.diagram("A --> B").format("png").build()
        self.assertEqual(self._load_file('png_diag.html'),
                         self.md.convert(text))

    def test_arg_format_svg(self):
        """
        Test for the correct parsing of the format argument, generating a svg image
        """
        text = self.text_builder.diagram("A --> B").format("svg").build()
        self.assertEqual(self._load_file('svg_diag.html'),
                         self.md.convert(text))

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
        text = self.text_builder.text('Paragraph before.\n\n')\
                                .diagram('A --> B')\
                                .text('\nMiddle paragraph.\n\n')\
                                .diagram('A <- B')\
                                .text('\nParagraph after.\n\n')\
                                .build()
        self.assertEqual(self._load_file('multiple_diag.html'),
                         self.md.convert(text))

    def test_other_fenced_code(self):
        """
        Test the coexistence of diagrams and other fenced code
        """
        text = self.text_builder.text('```bash\nls -l\n```\n')\
                                .text('\nA paragraph\n\n')\
                                .diagram('A --> B')\
                                .text('\nAnother paragraph\n')\
                                .build()
        self.assertEqual(self._load_file('code_and_diag.html'),
                         self.md.convert(text))
