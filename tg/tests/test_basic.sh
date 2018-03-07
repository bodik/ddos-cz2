#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh



RAWCONFIG=$(mktemp /tmp/tg2_test_basic_XXXXXX)
echo "{ 0 }" > $RAWCONFIG



# test send number of packets
NUMBER=$(($(random_byte)+1))
run_and_display RawConfig --filename ${RAWCONFIG} --num ${NUMBER}
check_value "scapy_display.summary.count: ${NUMBER}"


# test send number of packets for time at specified rate
NUMBER=4
run_and_display RawConfig --filename ${RAWCONFIG} --time ${NUMBER} --rate 1pps
check_value "scapy_display.summary.count: ${NUMBER}"



rm -f ${RAWCONFIG}
cleanup
rreturn 0 "$0"
