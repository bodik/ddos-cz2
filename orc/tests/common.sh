#!/bin/sh


rreturn() {
	RET=$1
	MSG=$2
	if [ $RET -eq 0 ]; then
		echo "RESULT: OK $MSG"
		exit 0
	else
		echo "RESULT: FAILED $MSG"
		exit 1
	fi
}


router_start() {
	export  ROUTER_PORT=$(python -c "import random; print(random.randint(64000,65000))")

	ROUTER_TMPCONFIG="/tmp/orc_tmpconfig.$$.json"
	cat << __EOF__ > ${ROUTER_TMPCONFIG}
{
	"websocket": {
		"address": "localhost:${ROUTER_PORT}"
	},
	"router": {
		"realms": [
			{
				"uri": "testrealm",
				"strict_uri": false,
				"allow_disclose": true,
				"anonymous_auth": true
			}
		],
		"debug": true
	}
}
__EOF__

	unset ROUTER_PID
	${BASEDIR}/router -c ${ROUTER_TMPCONFIG} 1>/dev/null &
	export ROUTER_PID=$!
	sleep 1
}

router_stop() {
	kill -TERM ${ROUTER_PID}
	wait ${ROUTER_PID}
	rm ${ROUTER_TMPCONFIG}
}


BASEDIR="$(readlink -f $(dirname $(readlink -f $0))/..)"
