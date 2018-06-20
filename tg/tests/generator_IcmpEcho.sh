#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP4_TTL=3
IP4_SOURCE=$(random_ipv4)
IP4_DESTINATION=$(random_ipv4)
ICMPECHO_IDENTIFIER=$(random_byte)
ICMPECHO_SEQUENCE_NUMBER=$(random_byte)
ICMPECHO_DATA="$(random_mac)$(random_mac)"



run_and_display IcmpEcho \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip4_ttl ${IP4_TTL} \
	--ip4_source_address ${IP4_SOURCE} \
	--ip4_destination_address ${IP4_DESTINATION} \
	--icmpecho_identifier ${ICMPECHO_IDENTIFIER} \
	--icmpecho_sequence_number ${ICMPECHO_SEQUENCE_NUMBER} \
	--icmpecho_data ${ICMPECHO_DATA}



check_value "IP.len: $((20+8+34))"
check_value "IP.ttl: ${IP4_TTL}"
check_value "IP.proto: 1"
check_value "IP.src: ${IP4_SOURCE}"
check_value "IP.dst: ${IP4_DESTINATION}"

check_value "ICMP.type: 8"
check_value "ICMP.code: 0"
check_value "ICMP.id: ${ICMPECHO_IDENTIFIER}"
check_value "ICMP.seq: ${ICMPECHO_SEQUENCE_NUMBER}"
check_value "Raw.load: '${ICMPECHO_DATA}'"



cleanup
rreturn 0 "$0"
