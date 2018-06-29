#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


router_start

netstat -nlpa | grep "${PID}/nexusd" | grep LISTEN | grep ":${PORT}"
if [ $? -ne 0 ]; then
	rreturn 1 "$0 nexus router"
fi

router_stop


rreturn 0 "$0"
