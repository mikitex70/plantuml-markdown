"""Unit tests for PlantUMLIncluder include-line handling (no rendering)."""

import pytest

from plantuml_markdown.plantuml_markdown import PlantUMLIncluder


@pytest.fixture()
def includer():
    return PlantUMLIncluder("uml", False, [r"^[Cc]4.*$"], False)


def test_includesub_returned_untouched(includer):
    line = "!includesub foo!bar"
    assert includer._readInclLine(line, ["."]) == line


def test_bare_include_returned_untouched(includer):
    line = "!include"
    assert includer._readInclLine(line, ["."]) == line


def test_url_include_returned_untouched(includer):
    line = "!include https://example.com/lib.puml"
    assert includer._readInclLine(line, ["."]) == line


def test_stdlib_include_returned_untouched(includer):
    line = "!include <archimate/Archimate>"
    assert includer._readInclLine(line, ["."]) == line


def test_missing_local_file_still_raises(includer):
    with pytest.raises(FileNotFoundError):
        includer._readInclLine("!include does-not-exist-12345.puml", ["."])
