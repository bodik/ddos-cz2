#!/usr/bin/python
"""layers implementation"""

import socket
import tg



#====================================================================
class Ethernet(object):
	"""layer ethernet impl"""

	HEADER_LENGTH = 14
	TEMPLATE = """
/* eth destination mac */		{eth_destination_mac},
/* eth source mac */			{eth_source_mac},
/* eth protocol */			c16({eth_protocol}),
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--eth_source_mac", help="eg. aa:bb:cc:dd:ee:ff")
		parser.add_argument("--eth_destination_mac", help="eg. aa:bb:cc:dd:ee:ff")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields
		source_mac defaults to corresponding addr
		destination_mac defaults to resolved gateway addr"""

		if not fields["eth_source_mac"]:
			fields["eth_source_mac"] = tg.utils.interface_mac(fields["dev"])
		fields["eth_source_mac"] = tg.utils.trafgen_format_mac(fields["eth_source_mac"])

		if not fields["eth_destination_mac"]:
			gwip = tg.utils.interface_gateway_ip(fields["dev"])
			fields["eth_destination_mac"] = tg.utils.ip_to_mac(gwip, fields["dev"])
		fields["eth_destination_mac"] = tg.utils.trafgen_format_mac(fields["eth_destination_mac"])

		return fields



#====================================================================
class Ip4(object):
	"""layer ip4 impl"""

	HEADER_LENGTH = 20
	TEMPLATE = """
/* ip4 version, ihl, tos */		0b01000101, 0,
/* ip4 total length */			c16({ip4_total_length}),
/* ip4 ipid */				drnd(2),
/* ip4 flags, fragment offset */	0b01000000, 0,
/* ip4 ttl */				{ip4_ttl},
/* ip4 protocol */			{ip4_protocol},
/* ip4 checksum */			IP_CSUM_DEFAULT,
/* ip4 source ip */			{ip4_source_address},
/* ip4 destination ip */		{ip4_destination_address},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--ip4_ttl", default=21)
		parser.add_argument("--ip4_source_address", default="self", help="eg. a.b.c.d|self|rnd|drnd")
		parser.add_argument("--ip4_destination_address", default="self", help="eg. a.b.c.d|self|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_ip4_address(fields, selector):
			"""handle self, rnd, drnd cases to field values"""

			if fields[selector] == "self":
				fields[selector] = tg.utils.interface_ip(fields["dev"])
			elif fields[selector] in ["rnd", "drnd"]:
				tmp = tg.utils.interface_ip(fields["dev"]).split(".")
				tmp[-1] = "%s(1)" % fields[selector]
				fields[selector] = ".".join(tmp)
			fields[selector] = tg.utils.trafgen_format_ip(fields[selector])
			return fields

		fields = process_ip4_address(fields, "ip4_source_address")
		fields = process_ip4_address(fields, "ip4_destination_address")
		return fields



#====================================================================

class Ip6(object):
	"""layer ip6 impl"""

	HEADER_LENGTH = 40
	TEMPLATE = """
/* ip6 version, traffic class (ECN, DS), flow label */		0b01100000, 0, 0, {ip6_flow_label},
/* ip6 payload length, next header, hop limit */		c16({ip6_payload_length}), {ip6_next_header}, {ip6_hop_limit},
/* ip6 source ip */						{ip6_source_address},
/* ip6 destination ip */					{ip6_destination_address},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--ip6_flow_label", default=2, help="lower byte of Flow Label field; int|rnd|drnd")
		parser.add_argument("--ip6_hop_limit", default=21)
		parser.add_argument("--ip6_source_address", default="self", help="eg. a:b:c:d::e|self|rnd|drnd")
		parser.add_argument("--ip6_destination_address", default="self", help="eg. a:b:c:d::e|self|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_flow_label(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(1)" % fields[selector]
			else:
				fields[selector] = "c8(%d)" % int(fields[selector])
			return fields


		def process_ip6_address(fields, selector):
			"""handle self, rnd, drnd cases to field values"""

			if fields[selector] == "self":
				fields[selector] = tg.utils.interface_ip(fields["dev"], socket.AF_INET6)
				fields[selector] = tg.utils.trafgen_format_ip(fields[selector])
			elif fields[selector] in ["rnd", "drnd"]:
				tmp = tg.utils.interface_ip(fields["dev"], socket.AF_INET6)
				tmp = tg.utils.trafgen_format_ip(tmp).split(",")
				tmp[-1] = "%s(2)" % fields[selector]
				fields[selector] = ",".join(tmp)
			else:
				fields[selector] = tg.utils.trafgen_format_ip(fields[selector])

			return fields

		fields = process_flow_label(fields, "ip6_flow_label")
		fields = process_ip6_address(fields, "ip6_source_address")
		fields = process_ip6_address(fields, "ip6_destination_address")
		return fields



#====================================================================
class Udp(object):
	"""layer udp"""

	HEADER_LENGTH = 8
	TEMPLATE = """
/* udp source port */			{udp_source_port},
/* udp destination port */		{udp_destination_port},
/* udp total length */			c16({udp_total_length}),
/* udp checksum */			c16(0),
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--udp_source_port", default=12345, help="eg. 123|rnd|drnd")
		parser.add_argument("--udp_destination_port", default=12345, help="eg. 123|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_port(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(2)" % fields[selector]
			else:
				fields[selector] = "c16(%d)" % int(fields[selector])
			return fields

		fields = process_port(fields, "udp_source_port")
		fields = process_port(fields, "udp_destination_port")
		return fields



#====================================================================
class Tcp(object):
	"""layer tcp"""

	HEADER_LENGTH = 20
	TEMPLATE = """
/* tcp source port */			{tcp_source_port},
/* tco destination port */		{tcp_destination_port},
/* tcp sequence number */		{tcp_sequence_number},
/* tcp acknowledgment number */		{tcp_acknowledgment_number},
/* tcp offset, reserver, flags */	c16((5 << 12) | {tcp_flags}),
/* tcp window size */			{tcp_window_size},
/* tcp checksum */			TCP_CSUM_DEFAULT,
/* tcp urgent pointer */		0x00, 0x00,
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--tcp_source_port", default=12345, help="eg. 123|rnd|drnd")
		parser.add_argument("--tcp_destination_port", default=12345, help="eg. 123|rnd|drnd")
		parser.add_argument("--tcp_sequence_number", default="drnd", help="eg. 123|rnd|drnd")
		parser.add_argument("--tcp_acknowledgment_number", default=0, help="eg. 123|rnd|drnd")
		parser.add_argument("--tcp_flags", default="S", help="eg. CEUAPRSF (not N)")
		parser.add_argument("--tcp_window_size", default=65001, help="eg. 123|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_port(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(2)" % fields[selector]
			else:
				fields[selector] = "c16(%d)" % int(fields[selector])
			return fields

		def process_sa_number(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(4)" % fields[selector]
			else:
				fields[selector] = "c32(%d)" % int(fields[selector])
			return fields

		def process_flags(fields, selector):
			"""handle tcp flags from argument"""

			tran = { \
				"C": "TCP_FLAG_CWR", "E": "TCP_FLAG_ECE", "U": "TCP_FLAG_URG", "A": "TCP_FLAG_ACK",
				"P": "TCP_FLAG_PSH", "R": "TCP_FLAG_RST", "S": "TCP_FLAG_SYN", "F": "TCP_FLAG_FIN"}
			fields[selector] = "|".join([tran[x] for x in fields[selector]])
			return fields

		fields = process_port(fields, "tcp_source_port")
		fields = process_port(fields, "tcp_destination_port")
		fields = process_sa_number(fields, "tcp_sequence_number")
		fields = process_sa_number(fields, "tcp_acknowledgment_number")
		fields = process_flags(fields, "tcp_flags")
		fields = process_port(fields, "tcp_window_size")
		return fields



#====================================================================
class IcmpEcho(object):
	"""simplified icmp+echo message"""

	HEADER_LENGTH = 8
	TEMPLATE = """
/* icmp type, icmp code */			8, 0,
/* icmp checksum(ETH_HLEN+IP4_HLEN, END) */	csumicmp(34, {icmpecho_payload_end}),
/* icmpecho type identifier */			{icmpecho_identifier},
/* icmpecho type sequence */			{icmpecho_sequence_number},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--icmpecho_identifier", default=0, help="eg. 123|rnd|drnd")
		parser.add_argument("--icmpecho_sequence_number", default=0, help="eg. 123|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_options_numbers(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(2)" % fields[selector]
			else:
				fields[selector] = "c16(%d)" % int(fields[selector])
			return fields

		fields = process_options_numbers(fields, "icmpecho_identifier")
		fields = process_options_numbers(fields, "icmpecho_sequence_number")
		return fields



#====================================================================
class Icmp6Echo(object):
	"""simplified icmp6+echo message"""

	HEADER_LENGTH = 8
	TEMPLATE = """
/* icmp6 type, icmp6 code */		128, 0,
/* icmp6 checksum */			csumicmp6(14,54),
/* icmp6echo type identifier */		{icmp6echo_identifier},
/* icmp6echo type sequence */		{icmp6echo_sequence_number},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--icmp6echo_identifier", default=0, help="eg. 123|rnd|drnd")
		parser.add_argument("--icmp6echo_sequence_number", default=0, help="eg. 123|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_options_numbers(fields, selector):
			"""handle rnd, drnd cases to field values"""

			if fields[selector] in ["rnd", "drnd"]:
				fields[selector] = "%s(2)" % fields[selector]
			else:
				fields[selector] = "c16(%d)" % int(fields[selector])
			return fields

		fields = process_options_numbers(fields, "icmp6echo_identifier")
		fields = process_options_numbers(fields, "icmp6echo_sequence_number")
		return fields
