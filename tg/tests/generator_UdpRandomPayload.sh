#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP_TTL=3
IP_SOURCE=$(random_ipv4)
IP_DESTINATION=$(random_ipv4)
UDP_SOURCE=$(random_int)
UDP_DESTINATION=$(random_int)
PAYLOAD_LENGTH=$(random_byte)



run_and_display UdpRandomPayload \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip_ttl ${IP_TTL} \
	--ip_source_address ${IP_SOURCE} \
	--ip_destination_address ${IP_DESTINATION} \
	--udp_source_port ${UDP_SOURCE} \
	--udp_destination_port ${UDP_DESTINATION} \
	--length ${PAYLOAD_LENGTH}



check_value "IP.len: $((20+8+${PAYLOAD_LENGTH}))"
check_value "IP.ttl: ${IP_TTL}"
check_value "IP.proto: 17"
check_value "IP.src: ${IP_SOURCE}"
check_value "IP.dst: ${IP_DESTINATION}"

check_value "UDP.sport: ${UDP_SOURCE}"
check_value "UDP.dport: ${UDP_DESTINATION}"
check_value "UDP.len: $((8+${PAYLOAD_LENGTH}))"



cleanup
rreturn 0 "$0"
