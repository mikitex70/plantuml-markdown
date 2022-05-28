#!/usr/bin/env bash

[[ -d "build" ]] && rm -rf build
[[ -d "dist"  ]] && rm -rf dist

# Build package for Python 3
. .env3*/bin/activate
pip install setuptools twine wheel
python setup.py bdist_wheel

# Check that packages are ok
twine check dist/*

deactivate
