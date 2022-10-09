[![Build Status](https://travis-ci.org/mikitex70/plantuml-markdown.svg?branch=master)](https://travis-ci.org/mikitex70/plantuml-markdown)

[PlantUML][] Extension for [Python-Markdown][]
==============================================

* [Introduction](#introduction)
* [Installation](#installation)
  * [Using a local plantUML binary](#using-a-local-plantuml-binary)
  * [Using a remote server](#using-a-remote-server)
    * [Using a PlantUML server](#using-a-plantuml-server)
    * [Using a Kroki server](#using-a-kroki-server)
    * [File inclusion management](#file-inclusion-management)
* [Plugin options](#plugin-options)
  * [A note on the `priority` configuration](#a-note-on-the-priority-configuration)
* [Running tests](#running-tests)
* [Running tests using Docker](#running-tests-using-docker)

Introduction
------------

This plugin implements a block extension that can be used to specify a [PlantUML] diagram that will be converted into an
image and inserted into the document.

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

Options are optional (otherwise the wouldn't be options), but if present must be specified in the order 
`format`, `classes`, `alt`, `title`, `width`, `height`, and `source`.
The option value may be enclosed in single or double quotes.

Supported values for `format` parameter are:

* `png`: HTML `img` tag with embedded png image
* `svg`: HTML `img` tag with embedded svg image (links are not navigable)
* `svg_object`: HTML `object` tag with embedded svg image (links are navigable)
* `svg_inline`: HTML5 `svg` tag with inline svg image source (links are navigable, can be manipulated with CSS rules)
* `txt`: plain text diagrams.

The `width` and `height` options must include a [CSS unit](https://www.w3schools.com/cssref/css_units.asp).

`source` parameter is used for inclusion of an external source diagram instead on an inline code. Here's an example in
GitLab/GitHub block syntax.

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
save the following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
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

The same thing can be done using the environment variable `_JAVA_OPTIONS`, which is read by default by the `java`
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

### Using a remote server

#### Using a PlantUML server

From version `2.0` a [PlantUML server] can be used for rendering diagrams. This speedups a
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
  encoding: utf-8                           # character encoding for external files (default utf-8)
  title: UML diagram                        # default title (tooltip) for diagram images
  alt: UML diagram image                    # default `alt` attribute for diagram images
  priority: 30                              # plugin priority; the higher, the sooner will be applied (default 30)
  http_method: GET                          # GET or POST  - note that plantuml.com only supports GET (default GET)       
  fallback_to_get: True                     # When using POST, should GET be used as fallback (POST will fail if @startuml/@enduml tags not used) (default True)
  theme: bluegray                           # theme to be set, can be overridden inside puml files, (default none)
  puml_notheme_cmdlist: [                             
                          'version', 
                          'listfonts', 
                          'stdlib', 
                          'license'
                        ]                   # theme will not be set if listed commands present (default as listed)
```

Then you need to specify the configuration file on the command line:

    markdown_py -x plantuml_markdown -c myconfig.yml mydoc.md > out.html

#### Using a Kroki server

Starting from version `3.7.0` a [Kroki] server can be used as an alternative of [PlantUML server].
The configuration is similar, only use the `server_kroki` configuration property instead of the `server` property.

#### File inclusion management

Usually, remote servers, for security reasons, do not allow arbitrary '!include' instructions to be executed.

To try to bypass this limitation, the plugin behaves as follows:
* the inclusion of [stdlib](https://plantuml.com/stdlib) libraries is considered secure and managed by the server; 
  example `!include <C4/C4_Container>`
* if the source to be included starts with `http` or `https`, the inclusion can be handled by the server; be aware that 
  the server may refuse to include them ([Kroki] in an example)
* if the source name matches one of the regular expressions in the `server_include_whitelist` configuration, the file is
  assumed to be safe for the server; an example is `!include C4/C4_Container.puml` with the server [Kroki], which has a
  copy of the C4 library internally
* otherwise, it is assumed that the file is local and that the `include` statement is replaced with the contents of the 
  file before sending it to the remote server. This behavior can be changed by declaring an appropriate regular
  expression in `server_include_whitelist` or by adding a comment to the line:
    * if the comment begins with `local`, include is forced local; e.g. `!include C4/C4_Container.puml ' local file`
      will search and read the local file `C4/C4_Container.puml`
    * if the comment begins with `remote`, include is treated as a server side include;
      for example `!include my_configuration.puml 'server-side include`

Plugin options
--------------

The plugin has several configuration option:

* `alt`: text to show when image is not available. Defaults to `uml diagram`
* `base_dir`: path where to search for external diagrams files
* `cachedir`: directory for caching of diagrams. Defaults to `''`, no caching
* `classes`: space separated list of classes for the generated image. Defaults to `uml`
* `encoding`: character encoding for external files (see `source` parameter); default encoding is `utf-8`. Please note 
  that on Windows text files may use the `cp1252` as default encoding, so setting `encoding: cp1252` may fix incorrect 
  characters rendering.
* `fallback_to_get`: Fallback to `GET` if `POST` fails. Defaults to True
* `format`: format of image to generate (`png`, `svg`, `svg_object`, `svg_inline` or `txt`). Defaults to `png` (See 
  example section above for further explanations of the values for `format`)
* `http_method`: Http Method for server - `GET` or `POST`. "Defaults to `GET`
* `image_maps`: generate image maps if format is `png` and the diagram has hyperlinks; `true`, `on`, `yes` or `1` 
  activates image maps, everything else disables it. Defaults to `true`
* `kroki_server`: Kroki server url, as alternative to `server` for remote rendering (image maps mus be disabled 
  manually). Defaults to `''`, use PlantUML server if defined
* `priority`: extension priority. Higher values means the extension is applied sooner than others. Defaults to `30`
* `puml_notheme_cmdlist`: theme will not be set if listed commands present. Default list is
  `['version', 'listfonts', 'stdlib', 'license']`. **If modifying please copy the default list provided and append**
* `server`: PlantUML server url, for remote rendering. Defaults to `''`, use local command
* `server_include_whitelist`: List of regular expressions defining which include files are supported by the server. 
  Defaults to `[r'^c4.*$']` (all files starting with `c4`). **See [Inclusion Management](#inclusion-management) for 
  details**
* `theme`: Default Theme to use, will be overridden  by !theme directive. Defaults to blank i.e. Plantuml `none` theme
* `title`: tooltip for the diagram

For passing options to the `plantuml_plugin` see the documentation of the tool you are using.

For `markdown_py`, simply write a YAML file with the configurations and use the `-c` option on the command line.
See the [Using a PlantUML server](#using-plantuml-server) section for an example.

### A note on the `priority` configuration

With `markdownm_py` plugin extensions can conflict if they manipulate the same block of text. 
Examples are the [Fenced Code Blocks](https://python-markdown.github.io/extensions/fenced_code_blocks)
or [Snippets](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/) extensions.

Every plugin has a priority configured, most wants to be run as te first or the last plugin in the chain. The
`plantuml_markdown` plugin fits in the middle, trying to work as best without conflicting with other plugins.

If you are getting strange behaviours in conjunction with other plugins, you can use the `priority` configuration to
try to avoid the conflict, letting the plugin run before (higher value) or after other plugins (lower value).

As an example of possible conflicts see issue [#38](https://github.com/mikitex70/plantuml-markdown/issues/38).

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
nose2 --verbose -F
```

This command uses a custom version of the `plantuml` command which will download the expected version of [PlantUML] for
tests execution without clobbering the system.


Running tests using Docker
-------------------------

This requires `docker` and `docker-compose` to be installed

First setup a small python alpine image with all the dependencies pre-installed. 
```bash
docker-compose build
``` 

then run the container to automatically trigger tests and print the output mapping the contents of your workspace

```bash
docker-compose up
```

To set specific version of Markdown or Python:
```bash
PTYHON_VER=3.9 MARKDOWN_VER=3.3.7 docker-compose build && docker-compose up
```


[Python-Markdown]: https://python-markdown.github.io/
[PlantUML]: http://plantuml.sourceforge.net/
[PlantUML server]: http://plantuml.com/server
[Kroki]: https://kroki.io/
[Graphviz]: http://www.graphviz.org
[Gentoo]: http://www.gentoo.org
[layman]: http://wiki.gentoo.org/wiki/Layman
