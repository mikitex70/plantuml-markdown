[![Build Status](https://travis-ci.org/mikitex70/plantuml-markdown.svg?branch=master)](https://travis-ci.org/mikitex70/plantuml-markdown)

[PlantUML][] Extension for [Python-Markdown][]
==============================================

This plugin implements a block extension which can be used to specify a [PlantUML][] diagram which will be
converted into an image and inserted in the document.

Syntax:

```markdown
    ::uml:: [format="png|svg|txt"] [classes="class1 class2 ..."] [alt="text for alt"] [title="Text for title"]
      PlantUML script diagram
    ::end-uml::
```

Example:

```markdown
    ::uml:: format="png" classes="uml myDiagram" alt="My super diagram placeholder" title="My super diagram"
      Goofy ->  MickeyMouse: calls
      Goofy <-- MickeyMouse: responds
    ::end-uml::
```

The GitLab/GitHub block syntax is also recognized. Example:

    ```plantuml format="png" classes="uml myDiagram" alt="My super diagram placeholder" title="My super diagram"
      Goofy ->  MickeyMouse: calls
      Goofy <-- MickeyMouse: responds
    ```

Options are optional (otherwise the wouldn't be options), but if present must be specified in the order `format`, `classes`, `alt`, `title`.
The option value may be enclosed in single or double quotes.

Supported values for `format` parameter are:

* `png`: HTML `img` tag with embedded png image
* `svg`: HTML `img` tag with embedded svg image (links are not navigable)
* `svg_object`: HTML `object` tag with embedded svg image (links are navigable)
* `svg_inline`: HTML5 `svg` tag with inline svg image source (links are navigable, can be manipulated with CSS rules)
* `txt`: plain text diagrams.

Installation
------------
You need to install [PlantUML][] (see the site for details) and [Graphviz][] 2.26.3 or later.
The plugin expects a program `plantuml` in the classpath. If not installed by your package
manager, you can create a shell script and place it somewhere in the classpath. For example,
save te following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
`/opt/plantuml`):

```
    #!/bin/bash
    java -jar /opt/plantuml/plantuml.jar ${@}
```

On Windows can be used the following `plantuml.bat` (many thanks to [henn1001](https://github.com/henn1001)):

```
    @echo off
    set mypath=%~dp0
    
    setlocal
    set GRAPHVIZ_DOT=%mypath%\Graphviz\bin\dot.exe

    java -jar %mypath%\plantuml.jar %*
```

Make sure the `plantuml.bat` is on the path.

For [Gentoo Linux][Gentoo] there is an ebuild at http://gpo.zugaina.org/dev-util/plantuml/RDep: you can download
the ebuild and the `files` subfolder or you can add the `zugaina` repository with [layman][]
(recommended).

To use the plugin with [Python-Markdown][] you have three choices:

* do a simple `pip install plantuml-markdown`, and the plugin should be ready to be used
* copy the file `plantuml.py` in the `extensions` folder of [Python-Markdown][]. For example, for Python 2.7 you must
  do:
  
  ```console
  $ sudo cp plantuml.py /usr/lib/python27/site-packages/markdown/extensions/
  ```
* copy the file somewhere in your home. A good choice may be the `user-site` path, for example (`bash` syntax):

  ```console
  $ export INSTALLPATH="`python -m site --user-site`/plantuml-markdown"
  $ mkdir -p "$INSTALLPATH"
  $ cp plantuml.py "$INSTALLPATH/mdx_plantuml.py"
  $ export PYTHONPATH="$INSTALLPATH"
  ```
  
  You must export `PYTHONPATH` before running `markdown_py`, or you can put the definition in `~/.bashrc`.

After installed, you can use this plugin by activating it in the `markdown_py` command. For example:

    markdown_py -x plantuml mydoc.md > out.html

Running tests
-------------

The test execution requires a specific version of [PlantUML] (the image generated can be different with different [PlantUML] versions).

To run the tests, execute the following command:

```bash
PATH="$PATH:$PWD/test" python -m unittest discover -v -s test
```

This command uses a custom version of the `plantuml` command which will download the expected version of [PlantUML] for
tests execution without clobbering the system.


[Python-Markdown]: https://python-markdown.github.io/
[PlantUML]: http://plantuml.sourceforge.net/
[Graphviz]: http://www.graphviz.org
[Gentoo]: http://www.gentoo.org
[layman]: http://wiki.gentoo.org/wiki/Layman
