#!/bin/sh

if [ ! -d .git ]; then
	git clone https://haas.cesnet.cz/ddos-cz2.git
else
	git pull
fi
git remote set-url --push origin ssh://dev@haas.cesnet.cz:/data/ddos-cz2.git
