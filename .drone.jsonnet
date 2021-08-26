local Pipeline(image, markdown_ver) = {
  kind: "pipeline",
  type: "docker",
  name: "test_"+std.strReplace(image, ".", "-")+"_md"+std.strReplace(markdown_ver, ".", "-"),
  steps: [
    {
      name: "test",
      image: image,
      environment: {
        http_proxy: {
          from_secret: "http_proxy"
        }
      },
      commands: [
        "apt-get update -y",
        "apt-get install -y --no-install-recommends graphviz default-jdk-headless",
        "wget 'http://sourceforge.net/projects/plantuml/files/plantuml.1.2020.23.jar/download' -O /tmp/plantuml.1.2020.23.jar",
        'sed "s/Markdown/Markdown=='+markdown_ver+'/" requirements.txt > /tmp/requirements.txt',
        "cat test-requirements.txt >> /tmp/requirements.txt",
        "pip install -r /tmp/requirements.txt",
        'PATH="$PATH:$PWD/test" python -m unittest discover -v -s test'
      ]
    }
  ]
};

local MARKDOWN_VER = ["3.0.1", "3.1.1", "3.2.2", "3.3.3"];
local PYTHON_VER = ["python:3.6", "python:3.7", "python:3.8", "python:3.9"];

[Pipeline(python, markdown) for python in PYTHON_VER for markdown in MARKDOWN_VER]
