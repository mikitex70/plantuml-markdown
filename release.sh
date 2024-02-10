#!/usr/bin/env bash

[[ -d "build" ]] && rm -rf build
[[ -d "dist"  ]] && rm -rf dist

# Build package for Python 3
. .env3*/bin/activate
pip install setuptools twine wheel

python setup.py bdist_wheel sdist --formats tar
pushd dist >/dev/null || exit
    distrib=$(ls *.tar); distrib=${distrib/.tar/}
    mkdir -p ${distrib}
        cp ../requirements.txt ${distrib}
        tar rvf ${distrib}.tar ${distrib}/requirements.txt && gzip ${distrib}.tar
    rm -fr ${distrib}
popd >/dev/null || exit

# Check that packages are ok
twine check dist/*

deactivate
