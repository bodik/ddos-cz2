#!/bin/sh

if [ ! -d .git ]; then
        git clone https://gitlab.flab.cesnet.cz/bodik/ddos-cz2.git
else
        git pull
fi
git remote set-url --push origin git@gitlab.flab.cesnet.cz:bodik/ddos-cz2.git
