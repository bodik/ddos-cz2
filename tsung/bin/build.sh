#!/bin/sh

TSUNG_DIR="/opt/tsung"
TSUNG_VERSION="1.7.0"
TSUNG_SOURCE="tsung-${TSUNG_VERSION}.tar.gz"
TSUNG_SOURCE_DIR="tsung-${TSUNG_VERSION}"
TSUNG_URL="http://tsung.erlang-projects.org/dist/${TSUNG_SOURCE}"

apt-get update
apt-get install -y build-essential gnuplot-nox libtemplate-perl libhtml-template-perl libhtml-template-expr-perl erlang-dev erlang-src erlang-snmp erlang-inets erlang-p1-xml

cd /tmp
wget $TSUNG_URL -O $TSUNG_SOURCE
tar xzvf $TSUNG_SOURCE
cd $TSUNG_SOURCE_DIR

./configure --prefix=${TSUNG_DIR}
make
make install
