#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


router_start
TMPLOG="/tmp/orc_slave.$$.log"


${BASEDIR}/slave --server ws://localhost:${ROUTER_PORT} --realm testrealm --debug 1>${TMPLOG} 2>&1 &
PID=$!
sleep 3
kill -TERM ${PID}
wait ${PID}

grep "communicator joined .* SessionDetails(realm=<testrealm>" ${TMPLOG}
if [ $? -ne 0 ]; then
	router_stop
	rreturn 1 "$0 slave not joined"
fi


router_stop
rm ${TMPLOG}

rreturn 0 "$0"
