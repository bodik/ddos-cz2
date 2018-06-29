#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


router_start
TMPLOG="/tmp/orc_master.$$.log"
export PYTHONUNBUFFERED=1


${BASEDIR}/master --server ws://localhost:${ROUTER_PORT} --realm testrealm --ui listener --debug 1>${TMPLOG} 2>&1 &
PID=$!
sleep 3
kill -TERM ${PID}
wait ${PID}

grep "communicator joined .* SessionDetails(realm=<testrealm>" ${TMPLOG}
if [ $? -ne 0 ]; then
	router_stop
	rreturn 1 "$0 master listener not joined"
fi


echo "quit" | ${BASEDIR}/master --server ws://localhost:${ROUTER_PORT} --realm testrealm --ui commander --debug 1>${TMPLOG} 2>&1

grep "communicator joined .* SessionDetails(realm=<testrealm>" ${TMPLOG}
if [ $? -ne 0 ]; then
	router_stop
	rreturn 1 "$0 master commander not joined"
fi


router_stop
rm ${TMPLOG}

rreturn 0 "$0"
