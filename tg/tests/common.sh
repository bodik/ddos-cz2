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

random_byte() {
	python -c "import random; print random.randint(0,255)"
}

random_int() {
	python -c "import random; print random.randint(0,65535)"
}

random_mac() {
	python -c "import random; print ':'.join(['%02x' % random.randint(0,255) for x in range(6)])"
}

random_ipv4() {
	python -c "import random; print '.'.join([str(random.randint(0,255)) for x in range(4)])"
}

run_and_display() {
	GENERATOR=$1
	shift

	BASEDIR="$(readlink -f $(dirname $(readlink -f $0))/..)"
	TESTID_ETH_SOURCE_MAC="$(random_mac)"
	TESTID_ETH_DESTINATION_MAC="$(random_mac)"

	echo "INFO: test for ${GENERATOR} ${TESTID_FILE} ${TESTID_FILE_DISPLAYED}"
	${BASEDIR}/tg2 ${GENERATOR} --dev ${TESTID_FILE} --eth_source_mac ${TESTID_ETH_SOURCE_MAC} --eth_destination_mac ${TESTID_ETH_DESTINATION_MAC} --num 1 $@ --debug
	${BASEDIR}/bin/scapy_display.py ${TESTID_FILE} > ${TESTID_FILE_DISPLAYED}
}

cleanup() {
	rm -f ${TESTID_FILE}
	rm -f ${TESTID_FILE_DISPLAYED}
}

check_value() {
	grep -q "^$1" ${TESTID_FILE_DISPLAYED} || rreturn 1 "failed value [$1]"
}


TESTID="$$.$(date +%s)"
TESTID_FILE="/tmp/tg2_test_${TESTID}.pcap"
TESTID_FILE_DISPLAYED="/tmp/tg2_test_${TESTID}.pcap.displayed"
