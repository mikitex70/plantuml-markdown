#!/usr/bin/env bash

[[ -d "build" ]] && rm -rf build
[[ -d "dist"  ]] && rm -rf dist

# Build package for Python 2
[[ -d ".env27" ]] || python2.7 -m virtualenv .env27
. .env27/bin/activate
pip install setuptools twine wheel
python setup.py bdist_wheel

deactivate

# Build package for Python 3
[[ -d ".env36" ]] || python3.6 -m virtualenv .env36
. .env36/bin/activate
pip install setuptools twine wheel
python setup.py bdist_wheel

# Check that packages are ok
twine check dist/*

deactivate
