#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP6_FLOW_LABEL=$(random_byte)
IP6_HOP_LIMIT=3
IP6_SOURCE=$(random_ipv6)
IP6_DESTINATION=$(random_ipv6)
UDP_SOURCE=$(random_int)
UDP_DESTINATION=$(random_int)
PAYLOAD_LENGTH=$(random_byte)



run_and_display Udp6RandomPayload \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip6_flow_label ${IP6_FLOW_LABEL} \
	--ip6_hop_limit ${IP6_HOP_LIMIT} \
	--ip6_source_address ${IP6_SOURCE} \
	--ip6_destination_address ${IP6_DESTINATION} \
	--udp_source_port ${UDP_SOURCE} \
	--udp_destination_port ${UDP_DESTINATION} \
	--length ${PAYLOAD_LENGTH}



check_value "IPv6.version: 6"
check_value "IPv6.fl: ${IP6_FLOW_LABEL}"
check_value "IPv6.plen: $((8+${PAYLOAD_LENGTH}))"
check_value "IPv6.nh: 17"
check_value "IPv6.hlim: ${IP6_HOP_LIMIT}"
check_value "IPv6.src: ${IP6_SOURCE}"
check_value "IPv6.dst: ${IP6_DESTINATION}"

check_value "UDP.sport: ${UDP_SOURCE}"
check_value "UDP.dport: ${UDP_DESTINATION}"
check_value "UDP.len: $((8+${PAYLOAD_LENGTH}))"



cleanup
rreturn 0 "$0"
