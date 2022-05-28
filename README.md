[![Build Status](https://travis-ci.org/mikitex70/plantuml-markdown.svg?branch=master)](https://travis-ci.org/mikitex70/plantuml-markdown)

[PlantUML][] Extension for [Python-Markdown][]
==============================================

This plugin implements a block extension which can be used to specify a [PlantUML][] diagram which will be
converted into an image and inserted in the document.

Syntax:

```markdown
::uml:: [format="png|svg|txt"] [classes="class1 class2 ..."] [alt="text for alt"] [title="Text for title"] [width="300px"] [height="300px"]
  PlantUML script diagram
::end-uml::
```

Example:

```markdown
::uml:: format="png" classes="uml myDiagram" alt="My super diagram placeholder" title="My super diagram" width="300px" height="300px"
  Goofy ->  MickeyMouse: calls
  Goofy <-- MickeyMouse: responds
::end-uml::
```

The GitLab/GitHub block syntax is also recognized. Example:

    ```plantuml format="png" classes="uml myDiagram" alt="My super diagram placeholder" title="My super diagram" width="300px" height="300px"
      Goofy ->  MickeyMouse: calls
      Goofy <-- MickeyMouse: responds
    ```

Options are optional (otherwise the wouldn't be options), but if present must be specified in the order `format`, `classes`, `alt`, `title`, `width`, `height`, and `source`.
The option value may be enclosed in single or double quotes.

Supported values for `format` parameter are:

* `png`: HTML `img` tag with embedded png image
* `svg`: HTML `img` tag with embedded svg image (links are not navigable)
* `svg_object`: HTML `object` tag with embedded svg image (links are navigable)
* `svg_inline`: HTML5 `svg` tag with inline svg image source (links are navigable, can be manipulated with CSS rules)
* `txt`: plain text diagrams.

The `width` and `height` options must include a [CSS unit](https://www.w3schools.com/cssref/css_units.asp).

`source` parameter is used for inclusion of an external source diagram instead on an inline code. Here's an example in GitLab/GitHub block syntax.

> basic.puml

    @startuml
    title Authentication Sequence
        Alice->Bob: Authentication Request
        note right of Bob: Bob thinks about it
        Bob->Alice: Authentication Response
    @enduml

> index.md

    ```plantuml source="basic.puml"
    '' This code is appended to the contents of basic.puml
    Goofy ->  MickeyMouse: calls
    Goofy <-- MickeyMouse: responds
    ```

Installation
------------

To use the plugin with [Python-Markdown][] you have these choices:

* with `pip`, do a simple `pip install plantuml-markdown`, and the plugin should be ready to be used
* on Windows you can use [Chocolatey](https://chocolatey.org/), a package manager for Windows: do a 
  `choco install plantuml` and you are ready to work (this command will install all dependencies, Java and Graphviz
   included, see https://chocolatey.org/packages/plantuml for details)
* copy the file `plantuml-markdown.py` in the `extensions` folder of [Python-Markdown][]. For example, for Python 2.7
  you must do:
  
  ```console
  $ sudo cp plantuml-markdown.py /usr/lib/python27/site-packages/markdown/extensions/
  ```
* copy the file somewhere in your home. A good choice may be the `user-site` path, for example (`bash` syntax):

  ```console
  $ export INSTALLPATH="`python -m site --user-site`/plantuml-markdown"
  $ mkdir -p "$INSTALLPATH"
  $ cp plantuml-markdown.py "$INSTALLPATH/mdx_plantuml-markdown.py"
  $ export PYTHONPATH="$INSTALLPATH"
  ```
  
  You must export `PYTHONPATH` before running `markdown_py`, or you can put the definition in `~/.bashrc`.

After installed, you can use this plugin by activating it in the `markdown_py` command. For example:

    markdown_py -x plantuml_markdown mydoc.md > out.html

But before to use it, you need to configure which [PlantUML] binary to use: a local binary, or a remote server.

### Using a local PlantUML binary

You need to install [PlantUML][] (see the site for details) and [Graphviz][] 2.26.3 or later.
The plugin expects a program `plantuml` in the classpath. If not installed by your package
manager, you can create a shell script and place it somewhere in the classpath. For example,
save te following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
`/opt/plantuml`):

```
#!/bin/bash
java $PLANTUML_JAVAOPTS -jar /opt/plantuml/plantuml.jar ${@}
```

The `PLANTUML_JAVAOPTS` variable can be used to set specific Java options, such as memory tuning options,
or to set system variable used by PlantUML, such as then include search path. This would avoid modifications of the
`plantuml` script. 
For example, with a diagram like:

````
```plantuml
!include myDefs.puml

A --> B
```
````

you can do:

```
export PLANTUML_JAVAOPTS="-Dplantuml.include.path=$HOME/plantuml_defs"
markdown_py -x plantuml_markdown mydoc.md > out.html
```

The same thing can be done using the environment variable `_JAVA_OPTIONS`, which is readed by default by the `java`
executable.

On Windows can be used the following `plantuml.bat` (many thanks to [henn1001](https://github.com/henn1001)):

```
@echo off
set mypath=%~dp0

setlocal
set GRAPHVIZ_DOT=%mypath%\Graphviz\bin\dot.exe

java %PLANTUML_JAVAOPTS% -jar %mypath%\plantuml.jar %*
```

Make sure the `plantuml.bat` is on the path.

For [Gentoo Linux][Gentoo] there is an ebuild at http://gpo.zugaina.org/dev-util/plantuml/RDep: you can download
the ebuild and the `files` subfolder or you can add the `zugaina` repository with [layman][]
(recommended).

### <a name="using-plantuml-server"></a>Using a PlantUML server

From version `2.0` a [PlantUML server](http://plantuml.com/server) can be used for rendering diagrams. This speedups a
lot the diagrams rendering but needs to send the diagram source to a server.

You can download the [war](http://sourceforge.net/projects/plantuml/files/plantuml.war/download) and deploy in a servlet
container, or you can run it as a [docker container](https://hub.docker.com/r/plantuml/plantuml-server/).

In either cases you need to specify the URL of the server in a configuration file like:

```yaml
plantuml_markdown:
  server: http://www.plantuml.com/plantuml  # PlantUML server, for remote rendering
  # other global options
  cachedir: /tmp                            # set a non-empty value to enable caching
  base_dir: .                               # where to search for diagrams to include
  format: png                               # default diagram image format
  classes: class1,class2                    # default diagram classes
  title: UML diagram                        # default title (tooltip) for diagram images
  alt: UML diagram image                    # default `alt` attribute for diagram images
  priority: 23                              # plugin priority; the higher, the sooner will be applied (default 23)
```

Then you need to specify the configuration file on the command line:

    markdown_py -x plantuml_markdown -c myconfig.yml mydoc.md > out.html
    
Plugin options
--------------

The plugin has several configuration option:

* `classes`: space separated list of classes for the generated image. Defaults to `uml`
* `format`: format of image to generate (`png`, `svg` or `txt`). Defaults to `png`
* `alt`: text to show when image is not available. Defaults to `uml diagram`
* `title`: tooltip for the diagram
* `server`: PlantUML server url, for remote rendering. Defaults to `''`, use local command
* `cachedir`: directory for caching of diagrams. Defaults to `''`, no caching
* `priority`: extension priority. Higher values means the extension is applied sooner than others. Defaults to `23`
* `base_dir`: path where to search for external diagrams files
* `encoding`: character encoding for external files (see `source` parameter); default encoding is `utf-8`. Please note that on Windows text files may use the `cp1252` as default encoding, so setting `encoding: cp1252` may fix incorrect characters rendering.

For passing options to the `plantuml_plugin` see the documentation of the tool you are using.

For `markdown_py`, simply write a YAML file with the configurations and use the `-c` option on the command line.
See the [Using a PlantUML server](#using-plantuml-server) section for an example.

Running tests
-------------

`plantuml-markdown` is tested with Python >= 3.6 and `Markdown >= 3.0.1`. Older versions of Python or `Markdown` may
work, but if it doesn't I can't guarantee a fix as they are end-of-life versions.

The test execution requires a specific version of [PlantUML] (the image generated can be different with different 
[PlantUML] versions).

Before to run tests, install the required dependencies:

```bash
pip install -r test-requirements.txt
```

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
