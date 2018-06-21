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

cleanup() {
	rm -f ${TEST_LOG_FILE}
}


check_value() {
	grep -s -q "$1" ${TEST_LOG_FILE} || rreturn 1 "URI not found [/$1]"
}

run() {
        echo "INFO: test for tsung ${TEST_LOG_FILE}"
	URI=$1
	timeout 10 ${BASEDIR}/tests/test-http-server.py 2> ${TEST_LOG_FILE} &
        ${BASEDIR}/pytsung localhost --uri "${URI}" --port 54321 --clients localhost -m GET --users 1 --requests 1 || rreturn $? "$0 pytsung" 
}


BASEDIR="$(readlink -f $(dirname $(readlink -f $0))/..)"
TESTID="$$.$(date +%s)"
TEST_LOG_FILE="/tmp/tsung2_test_${TESTID}.log"
