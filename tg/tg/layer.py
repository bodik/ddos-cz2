#!/usr/bin/python
"""layers implementation"""

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

		parser.add_argument("--dev", help="output iface; defaults to iface with default gw; eg. eth0")
		parser.add_argument("--eth_source_mac", help="eg. aa:bb:cc:dd:ee:ff")
		parser.add_argument("--eth_destination_mac", help="eg. aa:bb:cc:dd:ee:ff")


	@staticmethod
	def process_fields(fields):
		"""process input parameters to fields
		dev defaults to interface with route
		source_mac defaults to corresponding addr
		destination_mac defaults to resolved gateway addr"""

		if not fields["dev"]:
			fields["dev"] = tg.utils.default_output_interface()

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
class Udp(object):
	"""layer udp"""

	HEADER_LENGTH = 8
	TEMPLATE = """
/* udp source port */			{source_port},
/* udp destination port */		{destination_port},
/* udp total length */			const16({udp_total_length}),
/* udp checksum */			const16(0),
"""


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--source_port", default=12345, help="eg. 123|rnd|drnd")
		parser.add_argument("--destination_port", default=12345, help="eg. 123|rnd|drnd")


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

		fields = process_port(fields, "source_port")
		fields = process_port(fields, "destination_port")
		return fields
