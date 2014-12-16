[PlantUML][] Extension for [Python-Markdown][]
==============================================

This plugin implements a block extension which can be used to specify a [PlantUML][] diagram which will be
converted into an image and inserted in the document.

Syntax:

    :::markdown
    ::uml:: [format="png|svg"] [classes="class1 class2 ..."] [alt="text for alt"]
      PlantUML script diagram
    ::end-uml::

Example:

    :::markdown
    ::uml:: format="png" classes="uml myDiagram" alt="My super diagram"
      Goofy ->  MickeyMouse: calls
      Goofy <-- MickeyMouse: responds
    ::end-uml::

Options are optional, but if present must be specified in the order format, classes, alt.
The option value may be enclosed in single or double quotes.

Installation
------------
You need to install [PlantUML][] (see the site for details) and [Graphviz][] 2.26.3 or later.
The plugin expects a program `plantuml` in the classpath. If not installed by your package
manager, you can create a shell script and place it somewhere in the classpath. For example,
save te following into `/usr/local/bin/plantuml` (supposing [PlantUML][] installed into
`/opt/plantuml`):

    :::
     #!/bin/bash
     java -jar /opt/plantuml/plantuml.jar ${@}

For [Gentoo Linux][Gentoo] there is an ebuild at http://gpo.zugaina.org/dev-util/plantuml/RDep: you can download
the ebuild and the `files` subfolder or you can add the `zugaina` repository with [layman][]
(reccomended).

[Python-Markdown]: http://pythonhosted.org/Markdown/
[PlantUML]: http://plantuml.sourceforge.net/
[Graphviz]: http://www.graphviz.org
[Gentoo]: http://www.gentoo.org
[layman]: http://wiki.gentoo.org/wiki/Layman
