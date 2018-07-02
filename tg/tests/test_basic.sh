#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh



RAWCONFIG=$(mktemp /tmp/tg2_test_basic_XXXXXX)
echo "{ 0 }" > $RAWCONFIG



# test send number of packets
NUMBER=$(($(random_byte)+1))
run_and_display RawConfig --filename ${RAWCONFIG} --num ${NUMBER}
check_value "scapy_display.summary.count: ${NUMBER}"
cleanup


# test send number of packets for time at specified rate
NUMBER=4
run_and_display RawConfig --filename ${RAWCONFIG} --time ${NUMBER} --rate 1pps
check_value "scapy_display.summary.count: ${NUMBER}"
cleanup


# test sigterm handling
NUMBER=3
run_and_display RawConfig --filename ${RAWCONFIG} --time $((2*${NUMBER})) --rate 1pps &
sleep ${NUMBER}
pkill --pgroup $$ --signal TERM --full "/usr/bin/python3 ${BASEDIR}/tg2"
wait
check_value "scapy_display.summary.count: ${NUMBER}"
cleanup


# test sigint handling
NUMBER=3
run_and_display RawConfig --filename ${RAWCONFIG} --time $((2*${NUMBER})) --rate 1pps &
sleep ${NUMBER}
pkill --pgroup $$ --signal INT --full "/usr/bin/python3 ${BASEDIR}/tg2"
wait
check_value "scapy_display.summary.count: ${NUMBER}"
cleanup



rm -f ${RAWCONFIG}
rreturn 0 "$0"
