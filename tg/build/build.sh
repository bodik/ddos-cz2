#!/bin/sh

#prologue
set -e
BUILD_AREA=/tmp/build_area
mkdir -p $BUILD_AREA
cd $BUILD_AREA || exit 1

puppet apply install.pp

git clone https://github.com/netsniff-ng/netsniff-ng

