#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP_TTL=3
IP_SOURCE=$(random_ipv4)
IP_DESTINATION=$(random_ipv4)
TCP_SOURCE=$(random_int)
TCP_DESTINATION=$(random_int)



run_and_display TcpHeader \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip_ttl ${IP_TTL} \
	--ip_source_address ${IP_SOURCE} \
	--ip_destination_address ${IP_DESTINATION} \
	--tcp_source_port ${TCP_SOURCE} \
	--tcp_destination_port ${TCP_DESTINATION} \
	--tcp_flag "SAC"



check_value "IP.len: 40"
check_value "IP.ttl: ${IP_TTL}"
check_value "IP.proto: 6"
check_value "IP.src: ${IP_SOURCE}"
check_value "IP.dst: ${IP_DESTINATION}"

check_value "TCP.sport: ${TCP_SOURCE}"
check_value "TCP.dport: ${TCP_DESTINATION}"
check_value "TCP.flags: 146 \[SAC\]"



cleanup
rreturn 0 "$0"
