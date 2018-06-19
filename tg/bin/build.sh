#!/bin/sh
set -e


# dependencies
apt-get install gcc cpp make pkg-config flex bison
apt-get install libnacl-dev libz-dev libncurses5-dev libnl-3-dev


# build
BUILD_AREA=/tmp/build_area
mkdir -p $BUILD_AREA
cd $BUILD_AREA || exit 1

if [ ! -d netsniff-ng ]; then
	#git clone https://github.com/netsniff-ng/netsniff-ng
	git clone https://github.com/bodik/netsniff-ng --branch feature-csumicmp6
	cd netsniff-ng
else
	cd netsniff-ng
	git pull
fi
./configure
make trafgen ifpps
