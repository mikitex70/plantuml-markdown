# PlantUML-Markdown Agent Instructions

## Project Overview

Python-Markdown extension that renders PlantUML diagrams in Markdown documents. Single package, single module architecture.

## Developer Commands

**Install dependencies with uv:**
```bash
uv sync
```

**Install dependencies with pip:**
```bash
pip install -r requirements.txt
pip install -r test-requirements.txt
```

**Run tests:**
```bash
nose2 --verbose -F
```
Tests use a custom `plantuml` wrapper in `test/` that downloads a specific PlantUML version (1.2020.23) to ensure consistent test output.

**Run tests with Docker:**
```bash
docker-compose build
docker-compose up
```
Optional: `PYTHON_VER=3.9 MARKDOWN_VER=3.3.7 docker-compose build && docker-compose up`

**Install locally:**
```bash
pip install -e .
```

**Pre-commit hooks:**
```bash
pre-commit install
```

## Architecture

- **Main module:** `plantuml_markdown/plantuml_markdown.py` - single file containing all logic
- **Entry point:** `plantuml_markdown/__init__.py` exports `PlantUMLMarkdownExtension`
- **Test files:** `test/test_plantuml.py`, `test/test_plantuml_fenced.py`, `test/test_plantuml_legacy.py`
- **Test fixtures:** `test/data/` contains expected HTML outputs and test diagrams

## Key Implementation Details

### Diagram Syntax Support
- `::uml:: ... ::end-uml::` block syntax
- Fenced code blocks: ```plantuml ... ``` or ```uml ... ```
- Options order: `id`, `format`, `classes`, `alt`, `title`, `width`, `height`, `source`

### Format Options
- `png`: HTML img with embedded base64 image (supports image maps)
- `svg`: HTML img with base64-encoded SVG (links not navigable)
- `svg_object`: HTML object tag (links navigable)
- `svg_inline`: Inline SVG element (links navigable, CSS manipulable)
- `txt`: Plain text diagram output

### Rendering Modes
- **Local:** Executes `plantuml_cmd` (default: `plantuml`) with `-p` flag
- **Remote:** POST/GET to configured PlantUML/Kroki servers with compressed diagram data
- Servers tried in order until one succeeds

### Include Handling
The `PlantUMLIncluder` class recursively resolves `!include` directives:
- Stdlib includes (`!include <...>`) passed to server
- HTTP/HTTPS includes passed to server
- Local includes resolved from `base_dir` paths
- `server_include_whitelist` config controls server-side includes
- `local`/`remote` comments force include behavior

### Caching
When `cachedir` is set, diagrams are cached by Adler32 hash of source code.

## Configuration

Global config via YAML file passed to `markdown_py -c config.yml`:
- `servers`: List of rendering servers (preferred over deprecated `server`)
- `kroki_server`: Deprecated, use `servers` with `kroki: true`
- `base_dir`: Search paths for external diagram files
- `theme`: Default theme, overridden by `!theme` directive
- `puml_notheme_cmdlist`: Commands that prevent theme insertion
- `priority`: Extension priority (default 30, higher = applied sooner)

## Testing Notes

- Tests mock HTTP responses using `httpservermock`
- Test expectations in `test/data/*.html` compare rendered output
- SVG/png image data is normalized in comparisons
- `PLANTUML_SERVER` env var can redirect tests to remote server

## Build/Release

- **Version:** Defined in `pyproject.toml` and `setup.py` (sync both)
- **Build:** `python setup.py sdist bdist_wheel`
- **Upload:** Use `twine upload dist/*`
- **Changelog:** Maintained in `CHANGELOG.md`

## Common Gotchas

1. **Priority conflicts:** If fenced_code or snippets interfere, adjust `priority` config (higher value = earlier execution)
2. **Windows batch files:** Must start with `@echo off` to avoid extra output in images
3. **Image maps:** Only work with PNG format; Kroki servers don't support them
4. **SSL certificates:** Set `insecure: true` for self-signed certs (disables validation)
5. **POST vs GET:** PlantUML.com only supports GET; POST may fail with `@startuml` tags
6. **Theme insertion:** Automatic theme injection skips diagrams with `version`, `listfonts`, `stdlib`, or `license` commands

## Dependencies

- `Markdown`: Core markdown parsing
- `requests`: HTTP client for remote rendering
- `six`: Python 2/3 compatibility (legacy)
- `urllib3`: HTTP client library (used for SSL warning suppression)
- Dev deps: `pre-commit`, `commitizen`, `setuptools`, `twine`
- Test deps: `nose2`, `mock`, `httpservermock`, `mkdocs`, `pymdown-extensions`
