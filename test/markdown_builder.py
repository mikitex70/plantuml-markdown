import re

class MarkdownBuilder:

    def __init__(self, delimiter='```uml'):
        self._delimiter = delimiter
        self._end_delimiter = '::end-uml::' if delimiter == '::uml::' else re.sub(r'\w', '', delimiter)
        self._buffer = ""
        self._extended_syntax = False
        self._indent = 0
        self._reset_diagram()

    def _reset_diagram(self):
        """
        Clears the current diagram definition
        """
        self._format = ""
        self._class = ""
        self._alt = ""
        self._title = ""
        self._diagram_buffer = ""
        self._width = ""
        self._height = ""
        self._source = ""

    def _emit_diagram(self):
        """
        Appends the current diagram definition to the output buffer.
        After appending the diagram source, a new (empty) diagram is started
        """
        if self._diagram_buffer:
            delim = re.sub(r'(\W{3,})(\w+)', r'\1{\2', self._delimiter) if self._extended_syntax else self._delimiter
            args = self._format + self._class + self._alt + self._title + self._width + self._height + self._source
            self._buffer += (' '*self._indent)+delim+args+('}' if self._extended_syntax else '')
            self._buffer += "\n"+(' '*self._indent)+self._diagram_buffer+"\n"+(' '*self._indent)+self._end_delimiter+"\n"

        self._reset_diagram()

    def extended_syntax(self, extended=True):
        """
        Activates/deactivates the fenced code extended header syntax (like ```{uml args...}).
        :param extended: True to activate the extended syntax, False to deactivate
        :return: The object itself
        """
        self._extended_syntax = extended
        return self

    def alt(self, alt_text):
        """
        Defines the value for the 'alt' argument.
        :param alt_text: The text for the alt argument
        :return: The object itself
        """
        self._alt = " alt='%s'" % alt_text
        return self

    def title(self, title_text):
        """
        Defines the value for the 'title' argument.
        :param title_text: The text for the title argument
        :return: The object itself
        """
        self._title = " title='%s'" % title_text
        return self

    def classes(self, class_list):
        """
        Defines the value for the 'classes' argument.
        :param class_list: The text for the classes argument
        :return: The object itself
        """
        self._class = " classes='%s'" % class_list
        return self

    def format(self, fmt):
        """
        Defines the value for the 'format' argument.
        :param fmt: The text for the format argument
        :return: The object itself
        """
        self._format = " format='%s'" % fmt
        return self

    def width(self, w):
        """
        Define the maximum width of the diagram image.
        :param w: Max width, with unit (ex: "120px")
        :return: The object itself
        """
        self._width = " width='%s'" % w
        return self

    def height(self, h):
        """
        Define the maximum height of the diagram image.
        :param h: Max width, with unit (ex: "120px")
        :return: The object itself
        """
        self._height = " height='%s'" % h
        return self

    def source(self, file_path):
        """
        Sets inclusion of an external source diagram instead on an inline code.
        :param file_path: Path of the file containing the diagram source
        :return: The object itself
        """
        self._source = " source='%s'" % file_path
        return self

    def text(self, txt):
        """
        Adds a new text to the markdown source.
        The current diagram (if defined) will be flushed.
        :param txt: Text to add to the markdown source
        :return: The object itself
        """
        self._emit_diagram()
        self._buffer += txt
        return self

    def diagram(self, diag, indent=0):
        """
        Define a new diagram.
        :param diag: Diagram source
        :return: The object itself
        """
        self._emit_diagram()
        self._diagram_buffer = diag
        return self

    def indent(self, value):
        """
        Indent next block of text with the specified number of spaces.
        :param value: how many spaces to indent
        :return: The object itself
        """
        self._indent = value
        return self

    def build(self):
        """
        Return the markdown source build with the previous commands.
        :return: The markdown source
        """
        self._emit_diagram()
        return self._buffer
