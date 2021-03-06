#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh


ETH_SOURCE_MAC="$(random_mac)"
ETH_DESTINATION_MAC="$(random_mac)"
IP4_TTL=3
IP4_SOURCE=$(random_ip4)
IP4_DESTINATION=$(random_ip4)
UDP_SOURCE=$(random_int)
UDP_DESTINATION=$(random_int)
PAYLOAD_LENGTH=$(random_byte)



run_and_display UdpRandomPayload \
	--num 1 \
	--eth_source_mac ${ETH_SOURCE_MAC} \
	--eth_destination_mac ${ETH_DESTINATION_MAC} \
	--ip4_ttl ${IP4_TTL} \
	--ip4_source_address ${IP4_SOURCE} \
	--ip4_destination_address ${IP4_DESTINATION} \
	--udp_source_port ${UDP_SOURCE} \
	--udp_destination_port ${UDP_DESTINATION} \
	--length ${PAYLOAD_LENGTH}



check_value "IP.len: $((20+8+${PAYLOAD_LENGTH}))"
check_value "IP.ttl: ${IP4_TTL}"
check_value "IP.proto: 17"
check_value "IP.src: ${IP4_SOURCE}"
check_value "IP.dst: ${IP4_DESTINATION}"

check_value "UDP.sport: ${UDP_SOURCE}"
check_value "UDP.dport: ${UDP_DESTINATION}"
check_value "UDP.len: $((8+${PAYLOAD_LENGTH}))"



cleanup
rreturn 0 "$0"
