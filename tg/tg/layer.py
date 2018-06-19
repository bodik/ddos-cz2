#!/usr/bin/python
"""layers implementation"""

import socket
import tg



#====================================================================
class Ethernet(object):
	"""layer ethernet impl"""

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
class Ipv4(object):
	"""layer ipv4 impl"""

	HEADER_LENGTH = 20
	TEMPLATE = """
/* ipv4 version, ihl, tos */		0b01000101, 0,
/* ipv4 total length */			c16({ip_total_length}),
/* ipv4 ipid */				drnd(2),
/* ipv4 flags, fragment offset */	0b01000000, 0,
/* ipv4 ttl */				{ip_ttl},
/* ipv4 protocol */			{ip_protocol},
/* ipv4 checksum */			IP_CSUM_DEFAULT,
/* ipv4 source ip */			{ip_source_address},
/* ipv4 destination ip */		{ip_destination_address},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--ip_ttl", default=21)
		parser.add_argument("--ip_source_address", default="self", help="eg. a.b.c.d|self|rnd|drnd")
		parser.add_argument("--ip_destination_address", default="self", help="eg. a.b.c.d|self|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

		def process_ip_address(fields, selector):
			"""handle self, rnd, drnd cases to field values"""

			if fields[selector] == "self":
				fields[selector] = tg.utils.interface_ip(fields["dev"])
			elif fields[selector] in ["rnd", "drnd"]:
				tmp = tg.utils.interface_ip(fields["dev"]).split(".")
				tmp[-1] = "%s(1)" % fields[selector]
				fields[selector] = ".".join(tmp)
			fields[selector] = tg.utils.trafgen_format_ip(fields[selector])
			return fields

		fields = process_ip_address(fields, "ip_source_address")
		fields = process_ip_address(fields, "ip_destination_address")
		return fields



#====================================================================

class Ipv6(object):
	"""layer ipv6 impl"""

	HEADER_LENGTH = 40
	TEMPLATE = """
/* ipv6 version, traffic class (ECN, DS), flow label */		0b01100000, 0, 0, 1,
/* ipv6 total length, ipv6 next header, ipv6 hop limit */	c16({ip6_total_length}), {ip6_next_header}, {ip6_hop_limit},
/* ipv6 source ip */						{ip6_source_address},
/* ipv6 destination ip */					{ip6_destination_address},
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--ip6_hop_limit", default=21)
		parser.add_argument("--ip6_source_address", default="self", help="eg. a:b:c:d::e|self|rnd|drnd")
		parser.add_argument("--ip6_destination_address", default="self", help="eg. a:b:c:d::e|self|rnd|drnd")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields"""

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
