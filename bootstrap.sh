#!/bin/sh

if [ ! -d .git ]; then
        git clone https://rsyslog.metacentrum.cz/ddos-cz2.git
else
        git pull
fi
git remote set-url --push origin ssh://flab@esb.metacentrum.cz:/data/ddos-cz2.git
