#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP4_TTL=3
IP4_SOURCE=$(random_ip4)
IP4_DESTINATION=$(random_ip4)
TCP_SOURCE=$(random_int)
TCP_DESTINATION=$(random_int)



run_and_display TcpHeader \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip4_ttl ${IP4_TTL} \
	--ip4_source_address ${IP4_SOURCE} \
	--ip4_destination_address ${IP4_DESTINATION} \
	--tcp_source_port ${TCP_SOURCE} \
	--tcp_destination_port ${TCP_DESTINATION} \
	--tcp_flag "SAC"



check_value "IP.len: 40"
check_value "IP.ttl: ${IP4_TTL}"
check_value "IP.proto: 6"
check_value "IP.src: ${IP4_SOURCE}"
check_value "IP.dst: ${IP4_DESTINATION}"

check_value "TCP.sport: ${TCP_SOURCE}"
check_value "TCP.dport: ${TCP_DESTINATION}"
check_value "TCP.flags: 146 \[SAC\]"



cleanup
rreturn 0 "$0"
