#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP6_FLOW_LABEL=$(random_byte)
IP6_HOP_LIMIT=3
IP6_SOURCE=$(random_ipv6)
IP6_DESTINATION=$(random_ipv6)
TCP_SOURCE=$(random_int)
TCP_DESTINATION=$(random_int)



run_and_display Tcp6Header \
	--debug \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip6_flow_label ${IP6_FLOW_LABEL} \
	--ip6_hop_limit ${IP6_HOP_LIMIT} \
	--ip6_source_address ${IP6_SOURCE} \
	--ip6_destination_address ${IP6_DESTINATION} \
	--tcp_source_port ${TCP_SOURCE} \
	--tcp_destination_port ${TCP_DESTINATION} \
	--tcp_flag "SAC"



check_value "IPv6.version: 6"
check_value "IPv6.fl: ${IP6_FLOW_LABEL}"
check_value "IPv6.plen: 20"
check_value "IPv6.nh: 6"
check_value "IPv6.hlim: ${IP6_HOP_LIMIT}"
check_value "IPv6.src: ${IP6_SOURCE}"
check_value "IPv6.dst: ${IP6_DESTINATION}"

check_value "TCP.sport: ${TCP_SOURCE}"
check_value "TCP.dport: ${TCP_DESTINATION}"
check_value "TCP.flags: 146 \[SAC\]"



cleanup
rreturn 0 "$0"
