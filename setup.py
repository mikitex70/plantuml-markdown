import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name="plantuml-markdown",
    version="1.2.3rc2",
    author="Michele Tessaro",
    author_email="michele.tessaro@email.it",
    description="A PlantUML plugin for Markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mikitex70/plantuml-markdown",
    packages=setuptools.find_packages(),
    install_requires=['Markdown'],
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 6 - Mature",
        "Environment :: Plugins",
        "Topic :: Text Processing"
    ],
)
