#!/bin/sh

#prologue
set -e
BUILD_AREA=/tmp/build_area
mkdir -p $BUILD_AREA

puppet apply install.pp

cd $BUILD_AREA || exit 1
git clone https://github.com/netsniff-ng/netsniff-ng
make trafgen ifpps

