#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh



TESTPAYLOAD=$(mktemp /tmp/tg2_test_basic_XXXXXX)
echo "0" > $TESTPAYLOAD



# test send number of packets
NUMBER=$(random_byte)
run_and_display EthernetFilePayload --eth_protocol "0x0000" --filename ${TESTPAYLOAD} --num ${NUMBER}
check_value "scapy_display.summary.count: ${NUMBER}"


# test send number of packets for time at specified rate
NUMBER=4
run_and_display EthernetFilePayload --eth_protocol "0x0000" --filename ${TESTPAYLOAD} --time ${NUMBER} --rate 1pps
check_value "scapy_display.summary.count: ${NUMBER}"



rm -f ${TESTPAYLOAD}
cleanup
rreturn 0 "$0"
