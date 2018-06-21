#!/bin/sh

apt-get install python-virtualenv python3-virtualenv python3-pip

virtualenv -p python3 env
. env/bin/activate
pip3 install -r requirements.txt
