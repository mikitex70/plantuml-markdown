# Changelog


## 3.9.6 (2024-04-24)

### New

* `cachedir` is auto-created if missing (implements #96) [Michele Tessaro]


## 3.9.5 (2024-04-22)

### Fix

* Fixed caching with png diagrams without hyperlinks (fixes #27) [Michele Tessaro]


## 3.9.4 (2024-03-26)

### Changes

* Updated the CHANGELOG.md. [Michele Tessaro]

### Other

* Change packaging style to avoid having to do copying on installation. [Paul Harrison]

  the package registers itself as an extension from its pip installed location


## 3.9.3 (2024-02-10)

### Other

* Chore: add source tarball with requirements.txt at the root, for publishing to https://pypi.org/project/plantuml-markdown/#files. [Nick Boldt]

* Update README.md. [Mark Moretto]

  Aiming to clear-up some of the installation instructions.

* Update plantuml_markdown.py. [Mark Moretto]

  Updated `https://pythonhosted.org/..` URLs within file to `https://python-markdown.github.io/...`


## 3.9.2 (2023-06-22)

### Fix

* Fixed corrupted inline svg images (fixes #90) [Michele Tessaro]


## 3.9.1 (2023-04-27)

### Changes

* Updated the changelog. [Michele Tessaro]

### Fix

* Fixed handle of other diagram types with plantuml server. [Michele Tessaro]

  When using a PlantUML server the handling of non-uml diagrams
  (`startmindmap`, `startjson`, etc.) was building wrong open/close tags.

* Fixed urllib3 warning in output page (fixes #89) [Michele Tessaro]

  `urllib3` gives a warning when an insecure connection is used, and the
  warning is included in the output page.
  Now the warning is disabled if an insecure connection to a PlantUML
  server is used.


## 3.9.0 (2023-04-23)

### New

* Added support for other plantuml diagrams. [Michele Tessaro]

  Now can be used other kind of diagrams, like `startgantt`,
  `startmindmap`, `startjson` and many others.

* Added option for overriding plantuml command (resolves #87) [Michele Tessaro]

* Added plantuml config option (implements #88) [Michele Tessaro]


## 3.8.3 (2023-04-12)

### Fix

* Set default value for unsecure setting as boolean (fixes #86) [Michele Tessaro]


## 3.8.2 (2023-03-06)

### Changes

* Updated CHANGELOG for the new release. [Michele Tessaro]

### Fix

* Explicitly pass charset to plantuml. [Victor Westerhuis]

  The code is explicitly encoded to UTF-8, but plantuml gets to pick its own charset. On my Windows installation it picks codepage 1252 by default, leading to wrong characters in the output. UTF-8 should be available everywhere according to the [PlantUML documentation](https://plantuml.com/unicode).


## 3.8.1 (2023-01-29)

### New

* Added option for disabling SSL checks (refs #83) [Michele Tessaro]

  Added the `insecure` configuration option for disabling HTTPS SSL
  certificate validation.
  Set it to `True` when the PlantUML server uses self-signed certificates.


## 3.8.0 (2022-12-28)

### New

* Added `preserveAspectRatio` to inline SVG diagrams. [Michele Tessaro]

* Added `id` diagram option. [Michele Tessaro]

  When the `id` option is used, an `id` attribute will be generated for the
  diagram.
  This can be useful for referencing the diagram in CSS rules or
  Javascript code.

* Added `remove_inline_svg_size` config option. [Anders Norman]


## 3.7.3 (2022-10-16)

### New

* Added support for server-side C4 includes (refs #76) [Michele Tessaro]

  Added the `server_include_whilelist` configuration which is a list of
  regular expressions used to define which files can be safely included
  by the server.
  Defaults to `[r'^[Cc]4.*$']`, all C4 include files.


## 3.7.2 (2022-10-10)

### New

* Retry on server errors or rate limits when rendering remotely (refs #79) [Nejc Habjan]


## 3.7.1 (2022-10-07)

### Fix

* Do not create temp file with kroki (refs #77) [Nejc Habjan]


## 3.7.0 (2022-10-05)

### New

* Exposed error messages from kroki (refs #75) [Michele Tessaro]

  Error messages from Kroki server are rendered as text in the output.
  This is to overcome the problem that Kroki does not render errors as
  images as PluntUML does.

* Added kroki as rendering server (refs #75) [Michele Tessaro]

  With the plugin configuration `kroki_Server` is now possible to use a
  Kroki server fore remote rendering.
  Image maps are not supported by Kroki.

* Added option to disable image maps (refs #74) [Michele Tessaro]

### Changes

* Regenerated changelog. [Michele Tessaro]


## 3.6.3 (2022-08-01)

### Fix

* Fixed yaml rendering with remote server (fixes #72) [Michele Tessaro]

* Removed unused `plantuml` import. [Michele Tessaro]

* Doc: fix typos. [Kian-Meng Ang]


## 3.6.2 (2022-07-25)

### Fix

* Removed unused `plantuml` import. [Michele Tessaro]


## 3.6.1 (2022-07-23)

### Changes

* Regenerated the `CHANGELOG.md` [Michele Tessaro]

* Removed dependency from plantuml package (refs #70) [Michele Tessaro]

  The dependency from the `plantuml` package has been completely removed
  and the only small used method was imported in the sources.

### Fix

* Fixed typos in `CHANGELOG.md` [Michele Tessaro]

* Fixed external inclusions (fixes #71) [Michele Tessaro]

  Added parsing of `!define` PlantUML directives to be able to include
  external files when the base URL is define by a variable.
  See [AWS icons Hello World](https://github.com/awslabs/aws-icons-for-plantuml#hello-world)
  for an example.


## 3.6.0 (2022-07-20)

### New

* Added support for themes (implements #50) [Bharat Rajagopalan]

* Supported image maps from plantuml server. [Michele Tessaro]

  Now png image maps are used even if the rendering is done by a remote
  plantuml server.

### Changes

* Various README updates. [Bharat Rajagopalan]

* Added in the README an explanation of the priority config (refs #66) [Michele Tessaro]

* Remove md_globals kwarg. [Matt Riedemann]

  Markdown 3.4 dropped support for the md_globals
  kwarg:

  https://github.com/Python-Markdown/markdown/blob/master/docs/change_log/release-3.4.md#previously-deprecated-objects-have-been-removed

  Closes #67

* Updated notes on running tests. [Michele Tessaro]

### Fix

* Fixed tests. [Michele Tessaro]


## 3.5.3 (2022-05-28)

### Changes

* Fixed code indentation in README.md. [Michele Tessaro]

### Fix

* Fixed running on Windows (fixes #63) [Michele Tessaro]

  Fixed the condition for the detection of image maps: when there are no
  image maps, in Linux the output is `\n` while on Windows it is `\r\n`,
  so in Windows image maps were detected even if not present.


## 3.5.2 (2022-02-25)

### Fix

* Fixed error with external plantuml server (fixes #61) [Michele Tessaro]

  When using an external PlantUML server to render diagrams, if a diagram
  has syntax errors and the remote server returns an error code (HTTP >=
  400), and exception was thrown immediatly stopping markdown parsing.
  Now the error is intercepted and logged, and markdown can continue its
  work.


## 3.5.1 (2021-12-18)

### Changes

* Updated changelog for the new release. [Michele Tessaro]

### Fix

* There is no need to install uuid since Python 2.5 (refs #60) [Borys T]


## 3.5.0 (2021-11-23)

### New

* Add image map support. [Stéphane MORI]

  Some plantuml representation contains hyperlinks. Those hyperlinks trig
  the generation of a map tag. These map tag is linked to the generated
  image by usemap attribute which refer to the map name.

### Changes

* Update the changelog. [Michele Tessaro]


## 3.4.4 (2021-10-24)

### Fix

* Fix progression of parser (#57) [Spencer Gilson]


## 3.4.3 (2021-08-29)

### Changes

* Updated documentation for the new release. [Michele Tessaro]

### Fix

* Fixed read utf8 sources in Windows (refs #56) [Michele Tessaro]

  Now the `source` option expects files in the `utf8` encoding.
  In *nix nothing should change; Windows therefore uses `cp1252` as the
  default character encoding, so if you need to use that encoding you need
  to specify it in the plugin configuration options. Example:
  ```yaml
  plantuml_markdown:
      encoding: cp1252
  ```


## 3.4.2 (2020-12-19)

### Changes

* Updated CHANGELOG. [Michele Tessaro]

* Remove tests for python < 3.6. [Michele Tessaro]

  Python versions before 3.6 are now at end of life.
  `plantuml-markdown` will not be tested with those versions, and bugs
  will be fixed only if reproducible with more recent Python versions.

### Fix

* Fixed working with Markdown 3.3 (fixes #39) [Michele Tessaro]

* Fixed indentation handling (fixes #51) [Michele Tessaro]


## 3.4.1 (2020-10-28)

### Fix

* Fixed multiple mixed code blocks (fixes #45) [Michele Tessaro]

  Fixed parsing of mixed `fenced_code` and `plantuml_markdown` blocks in
  the same document.


## 3.4.0 (2020-08-23)

### New

* Capability to keep both inline and source data (implements #47) [Ihsan Topaloglu]

  As per discussed on https://github.com/mikitex70/plantuml-markdown/issues/47

### Changes

* Updated CHANGELOG.md. [Michele Tessaro]

* Update README.md (refs #47) [Ihsan Topaloglu]

* Update README.md (refs #47) [Ihsan Topaloglu]

  Readme update for the `source` inclusion feature that came with https://github.com/mikitex70/plantuml-markdown/releases/tag/3.3.0

### Fix

* Fixed uml code inside fenced code (fixes #45) [Michele Tessaro]

  UML source diagram inside a fenced code is now leaved untouched.


## 3.3.0 (2020-06-18)

### New

* Added support for loading plantuml from external files (refs #42) [Chalmela, Ravi]

### Changes

* Updated documentation. [Michele Tessaro]

* Updated documentation. [Michele Tessaro]

### Fix

* Fixed closing of object tag (fixes #44) [Michele Tessaro]


## 3.2.2 (2020-03-04)

### Fix

* Removed forgotten log level set to debug (fixes #41) [Michele Tessaro]


## 3.2.1 (2019-12-13)

### New

* Added support for Python 3.8. [Michele Tessaro]


## 3.2.0 (2019-12-08)

### New

* Added `priority` option to change plugin priority (refs #38) [Michele Tessaro]

  Now the plugin execution priority can be changed if you don't like
  default value.
  The default should be the most reasonable with most plugins.

### Changes

* Updated changelog. [Michele Tessaro]

* Documented how to set plantuml include search path (refs #37) [Michele Tessaro]


## 3.1.4 (2019-11-13)

### New

* Expand "~" in cachedir config. [Jean Jordaan]

### Changes

* Updated changelog for the new release. [Michele Tessaro]

### Fix

* Fixed special characters handling in alt and title (fixes #70) [Michele Tessaro]

* Fix brackets. [Jean Jordaan]


## 3.1.3 (2019-08-26)

### Changes

* Updated changelog for the new release. [Michele Tessaro]

* Updated changelog for the new release. [Michele Tessaro]

### Fix

* Fix rendering in indented blocks (fixes #31) [Grzegorz Adamiak]

  It fixes [issue][31] with rendering indented fenced blocks. They were
  rendered only when put at beginning of the line. To illustrate, this
  block was processed correctly

      ```plantuml
      A --> B : I am processed
      ```

  while a block nested under a list item (indented) was not processed

        * A list item with nested block

          ```plantuml
          A --> B : I am not processed
          ```

  [31]: https://github.com/mikitex70/plantuml-markdown/issues/31

  With this patch the block is converted into image and correctly put in
  the document tree allowing for images nested in other block elements,
  e.g. list items.


## 3.1.2 (2019-06-01)

### Fix

* Fixed pip installable packages (fixes #29, #30) [Michele Tessaro]


## 3.1.1 (2019-05-29)

### Fix

* Fixed compatibility with Markdown 2 (refs #29) [Michele Tessaro]


## 3.1.0 (2019-05-02)

### New

* Added diagram caching (implements #27) [Michele Tessaro]

  To activate caching define the configuration option `cachedir`.
  See the `README.md` for some detail.

### Changes

* Update changelog for the new release. [Michele Tessaro]

* Added installation instructions for `chocolatey` (refs #28) [Michele Tessaro]


## 3.0.0 (2019-03-31)

### New

* Allow percent sign in width and height options. [Mathias Lüdtke]

### Changes

* Updated documentation for new release. [Michele Tessaro]

### Fix

* Renamed module to `plantuml_markdown` (fixes #23) [Michele Tessaro]

  Renamed module from `plantuml-markdown` to `plantuml_markdown` to allow
  importing module in other python sources.
  This breaks compatibility: plugin configuration in `markdown_py` must be
  renamed too.


## 2.0.2 (2019-03-16)

### Changes

* Updated documentation for new release. [Michele Tessaro]

### Fix

* Fixed handling of unicode characters in svg_inline (refs #21) [Szymon Wilkołazki]


## 2.0.1 (2019-03-03)

### Changes

* Updated documentation for the new release. [Michele Tessaro]

### Fix

* Fixed package contents. [Michele Tessaro]


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
  shrunk keeping the aspect ratio.
  If there is not enough space in the page for the diagram, the image
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
  misspelled to `classes`.


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

  * base64 encoded SVGs, as Firefox doesn't handles plain SVGs
  * fixed the need of 2 empty lines for 'txt' diagrams
  * fixed newlines converted into br tags for 'txt' diagrams

* Correct path exists test. [Benjamin Henriet]

* Small documentation correction. [Michele]

* Little correction in documentation. [Michele]

* Some correction in markdown documentation syntax. [Michele]

* Some correction to documentation. [Michele]

### Other

* Removed the (useless) remove of the last line of source text block. [Michele Tessaro]

* Use inline images, NO MORE TEMPFILES!  Experimental 'txt' support. [kubilus1]

* Implemented a sort of caching for generated images. [Michele Tessaro]

  Image names are build from an hash code based on the diagram source.
  If the source diagram changes, the image maybe different and will be
  re-generated.
  Now images are generated only if not already present.

* Remove self from static method. [Benjamin Henriet]

* Remove self param from static method, disable image renaming/removing. [arye]

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


