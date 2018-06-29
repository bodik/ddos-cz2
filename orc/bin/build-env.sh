#!/bin/sh

BASE="$(dirname $(readlink -f $0))/.."

apt-get install python-virtualenv python3-virtualenv python3-pip

virtualenv -p python3 env
. env/bin/activate
pip3 install -r ${BASE}/etc/requirements.txt
