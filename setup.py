import setuptools
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md")) as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt')) as f:
    install_requirements = f.read().splitlines()

with open(path.join(here, 'test-requirements.txt')) as f:
    test_requirements = f.read().splitlines()

setuptools.setup(
    name="plantuml-markdown",
    version="3.4.2",
    author="Michele Tessaro",
    author_email="michele.tessaro@email.it",
    description="A PlantUML plugin for Markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=['Markdown', 'typesetting', 'include', 'plugin', 'extension'],
    url="https://github.com/mikitex70/plantuml-markdown",
    #packages=setuptools.find_packages(exclude=['test']),
    py_modules=['plantuml_markdown'],
    install_requires=install_requirements,
    tests_require=test_requirements,
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Markup :: HTML"
    ],
)
