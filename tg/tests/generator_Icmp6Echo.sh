#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP6_FLOW_LABEL=$(random_byte)
IP6_HOP_LIMIT=3
IP6_SOURCE=$(random_ip6)
IP6_DESTINATION=$(random_ip6)
ICMP6ECHO_IDENTIFIER=$(random_byte)
ICMP6ECHO_SEQUENCE_NUMBER=$(random_byte)
ICMP6ECHO_DATA="$(random_mac)"



run_and_display Icmp6Echo \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip6_flow_label ${IP6_FLOW_LABEL} \
	--ip6_hop_limit ${IP6_HOP_LIMIT} \
	--ip6_source_address ${IP6_SOURCE} \
	--ip6_destination_address ${IP6_DESTINATION} \
	--icmp6echo_identifier ${ICMP6ECHO_IDENTIFIER} \
	--icmp6echo_sequence_number ${ICMP6ECHO_SEQUENCE_NUMBER} \
	--icmp6echo_data ${ICMP6ECHO_DATA}



check_value "IPv6.version: 6"
check_value "IPv6.fl: ${IP6_FLOW_LABEL}"
check_value "IPv6.plen: $((8+17))"
check_value "IPv6.nh: 58"
check_value "IPv6.hlim: ${IP6_HOP_LIMIT}"
check_value "IPv6.src: ${IP6_SOURCE}"
check_value "IPv6.dst: ${IP6_DESTINATION}"

check_value "ICMPv6 Echo Request.type: 128"
check_value "ICMPv6 Echo Request.code: 0"
check_value "ICMPv6 Echo Request.id: ${ICMP6ECHO_IDENTIFIER}"
check_value "ICMPv6 Echo Request.seq: ${ICMP6ECHO_SEQUENCE_NUMBER}"



cleanup
rreturn 0 "$0"
