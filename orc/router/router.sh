#!/bin/sh

BASE="$(dirname $(readlink -f $0))"
${BASE}/nexusd -c ${BASE}/nexus.json
