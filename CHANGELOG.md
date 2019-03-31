# Changelog

## 3.0.0 (2019-03-31)

### New

* Allow percent sign in width and height options. [Mathias Lüdtke]

### Fix

* Renamed module to `plantuml_markdown` (fixes #23) [Michele Tessaro]

  Renamed module from `plantuml-markdown` to `plantuml_markdown` to allow
  importing module in other python sources.
  Thi breaks compatibility: plugin configuration in `markdown_py` must be
  renamed too.


## 2.0.2 (2019-03-16)

### New

* Added test to verify utf-8 character handling. [Michele Tessaro]

### Changes

* Updated documentation for new release. [Michele Tessaro]

### Fix

* Fixed handling of unicode characters in svg_inline (refs #21) [Szymon Wilkołazki]


## 2.0.1 (2019-03-03)

### Changes

* Updated documentation for the new release. [Michele Tessaro]

### Fix

* Fixed package contents. [Michele Tessaro]

* Fixed travis configuration. [Michele Tessaro]


## 2.0.0 (2019-03-02)

### New

* Added support for use a plantuml server (implements #19) [Michele Tessaro]

  Now for the diagram rendering can be used an external PlantUML server.
  This can speedup document generation when there are a lot of diagrams.

### Changes

* Updated documentation for new release. [Michele Tessaro]

### Fix

* Use preprocessors.register instead of (deprecated) add. [Johan]

* Fixed usage syntax. [Michele Tessaro]

  The `width` and `height` options are marked as optional.


## 1.4.0 (2018-11-24)

### New

* Added `width` and `height` attributes. [Michele Tessaro]

  The new attributes `width` and `height` can be used to limit image size:
  if the image dimension is bigger than values specified, they will be
  shrinked keeping the aspect ratio.
  If there is not enought space in the page fot the diagram, the image
  will be reduced.

### Changes

* Updated documentation for new release. [Michele Tessaro]

### Fix

* Fixed navigable links in inline SVG (resolves #18) [Michele Tessaro]


## 1.3.0 (2018-11-17)

### New

* Added support for clickable SVGs (closes #17) [Michele Tessaro]

  Added two new output formats:
  * `svg_object`: generated an `object` tag for displaing svg images
  * `svg_inline`: embedded the svg source image directly in the document

### Fix

* Fixed error when the output format is not recognized. [Michele Tessaro]


## 1.2.6 (2018-11-04)

### Changes

* Update documentation. [Michele Tessaro]

### Fix

* Fixed wrong `classes` HTML attribute (fixes #16) [Michele Tessaro]

  Fixed a type on the generated HTML code, the `class` attribute was
  mispelled to `classes`.


## 1.2.5 (2018-08-27)

### Fix

* Fixed running on Windows (refs #11) [Michele Tessaro]

  Thanks to henn1001 to pointing out a problem on Windows. See
  https://github.com/mikitex70/plantuml-markdown/issues/11#issuecomment-414057579
  for details.


## 1.2.4 (2018-07-15)

### New

* Added configuration for deployment to pypi and install with pip. [Michele Tessaro]

* Added configuration for deployment to pypi and install with pip. [Michele Tessaro]

### Changes

* Changes python-markdown project URL. [Fred Z]

### Fix

* Fixed package build for pip installation. [Michele Tessaro]


## 1.2.3 (2018-04-19)

### New

* Added some test. [Michele Tessaro]

* Added title macro option. [Michele Tessaro]

  Added a title option which would be used for generating the title
  (tooltip) of the diagrams in HTML rendering.

* Added GitLab compatibility (closes #7) [Michele Tessaro]

  Now the block diagram may be delimited also with the triple backtick
  character used in GitLab and others to delimit code blocks.
  See the README.md for more details.

* Added output path existence check. [Michele]

* Added source code. [Michele]

  Python-Markdown plugin for PlantUML.

### Fix

* Fixed running wiith Python 2.7. [Michele Tessaro]

* Fixed test execution with travis-ci. [Michele Tessaro]

* Fixed working with the fenced_code plugin (refs #8) [Michele Tessaro]

  Fixed diagram generation when used together with the fenced_code plugin.

* Fixed one-block diagrams parsing (fixes #9, #10) [Michele Tessaro]

  One block diagrams (without at least one empty line inside) were not
  correctly recognised.

* Minor fix in documentation. [Michele Tessaro]

* Fixed unicode characters in the macro options. [Michele Tessaro]

  Macro options parsing now will work correctly when using unicode
  characters (for example in the alt options).

* Fixed generation of class and alt image attributes. [Michele Tessaro]

  Images in the generated HTML were missing for the class and alt
  attributes.

* Fix an error with svg format. [jumpei-miyata]

* Fix regular expression. [jumpei-miyata]

* Some minor fixes. [Michele Tessaro]

  * base64 encoded SVGs, as Firefox doesn&#x27;t handles plain SVGs
  * fixed the need of 2 empty lines for &#x27;txt&#x27; diagrams
  * fixed newlines converted into br tags for &#x27;txt&#x27; diagrams

* Correct path exists test. [Benjamin Henriet]

* Small documentation correction. [Michele]

* Little correction in documentation. [Michele]

* Some correction in markdown documentation syntax. [Michele]

* Some correction to documentation. [Michele]

### Other

* Removed the (useless) remove of the last line of source text block. [Michele Tessaro]

* Use inline images, NO MORE TEMPFILES!  Experimental &#x27;txt&#x27; support. [kubilus1]

* Implemented a sort of caching for generated images. [Michele Tessaro]

  Image names are build from an hash code based on the diagram source.
  If the source diagram changes, the image maybe different and will be
  re-generated.
  Now images are generated only if not already present.

* Remove self from static method. [Benjamin Henriet]

* Remove self param from static method, diable image renaming/removing. [arye]

* Updated documentation for installation. [Michele]

  Added details on installing locally or globally.

* Adapted to work with Python 3. [Michele]

* Registered plugin after code block parser. [Michele]

  Registering the plugin after the code parser gives the possibility to
  write source uml code without being handled by this plugin and to
  present it as any other source code example.

* Keep temporary file if PlantUML fails. [Michele]

  The temporary file containing the PlantUML script can be used to
  identify syntax errors in the source MD document

* Initial commit. [Michele Tessaro]


