#!/usr/bin/env bash

[[ -d "build" ]] && rm -rf build
[[ -d "dist"  ]] && rm -rf dist

# Build wheel and sdist using Docker (pure Python: py3-none-any)
echo "Building wheel and sdist..."
docker run --rm -u $(id -u):$(id -g) -e HOME="/tmp" -v "$(pwd):/$(pwd)" -w "$(pwd)" python:3.11-slim \
    sh -c "pip install build && python -m build"

# Add requirements files to the source distribution
pushd dist >/dev/null || exit
    distrib=$(ls *.tar.gz); distrib=${distrib/.tar.gz/}
    gunzip ${distrib}.tar.gz
    mkdir -p ${distrib}
        cp ../requirements.txt ../test-requirements.txt ${distrib}
        tar rvf ${distrib}.tar ${distrib}/requirements.txt ${distrib}/test-requirements.txt
    rm -fr ${distrib}
    gzip ${distrib}.tar
popd >/dev/null || exit

# Check that packages are ok (using Docker since twine may not be installed locally)
echo "Checking packages..."
docker run --rm -v "$(pwd):/$(pwd)" -w "$(pwd)" python:3.11-slim \
    sh -c "pip install twine && twine check dist/*"
