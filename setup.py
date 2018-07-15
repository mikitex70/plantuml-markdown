import setuptools
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), "r") as f:
    long_description = f.read()
    
setuptools.setup(
    name="plantuml-markdown",
    version="1.2.4",
    author="Michele Tessaro",
    author_email="michele.tessaro@email.it",
    description="A PlantUML plugin for Markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords = ['Markdown', 'typesetting', 'include', 'plugin', 'extension'],
    url="https://github.com/mikitex70/plantuml-markdown",
    packages=['.'],
    install_requires=['Markdown'],
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
