import re

class MarkdownBuilder:

    def __init__(self, delimiter='```uml'):
        self._delimiter = delimiter
        self._end_delimiter = '::end-uml::' if delimiter == '::uml::' else re.sub(r'\w', '', delimiter)
        self._buffer = ""
        self._extended_syntax = False
        self._reset_diagram()

    def _reset_diagram(self):
        """
        Clears the current diagram definition
        """
        self._format = ""
        self._classes = ""
        self._alt = ""
        self._title = ""
        self._diagram_buffer = ""

    def _emit_diagram(self):
        """
        Appends the current diagram definition to the output buffer.
        After appending the diagram source, a new (empty) diagram is started
        """
        if self._diagram_buffer:
            delim = re.sub(r'(\W{3,})(\w+)', r'\1{\2', self._delimiter) if self._extended_syntax else self._delimiter
            args = self._format+self._classes+self._alt+self._title
            self._buffer += delim+args+('}' if self._extended_syntax else '')
            self._buffer += "\n"+self._diagram_buffer+"\n"+self._end_delimiter+"\n"

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
        self._classes = " classes='%s'" % class_list
        return self

    def format(self, fmt):
        """
        Defines the value for the 'format' argument.
        :param fmt: The text for the format argument
        :return: The object itself
        """
        self._format = " format='%s'" % fmt
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

    def diagram(self, diag):
        """
        Define a new diagram.
        :param diag: Diagram source
        :return: The object itself
        """
        self._emit_diagram()
        self._diagram_buffer = diag
        return self

    def build(self):
        """
        Return the markdown source build with the previous commands.
        :return: The markdown source
        """
        self._emit_diagram()
        return self._buffer
