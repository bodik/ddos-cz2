#!/bin/sh
set -e

BUILD_AREA=/tmp/build_area
mkdir -p $BUILD_AREA
cd $BUILD_AREA || exit 1

wget https://dl.google.com/go/go1.10.3.linux-amd64.tar.gz
tar xf go1.10.3.linux-amd64.tar.gz
GOROOT=$(pwd)/go
GOPATH=$(pwd)/golang
PATH=$GOPATH/bin:$GOROOT/bin:$PATH

go get github.com/gammazero/nexus/...
cd $GOPATH/src/github.com/gammazero/nexus/nexusd
go build
