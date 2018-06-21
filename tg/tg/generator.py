#!/usr/bin/python
"""generators implementation"""

import tg


#====================================================================
@tg.modreg.register
class RawConfig(object):
	"""generator impl - raw config generator"""

	TEMPLATE = """
/* rawconfig */				{rawconfig}
"""
	LAYERS = [TEMPLATE]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--filename", required=True, help="full payload filename")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		with open(fields["filename"], "r") as ftmp:
			fields["rawconfig"] = ftmp.read()
		return fields



#====================================================================
@tg.modreg.register
class UdpRandomPayload(object):
	"""generator impl - udp random payload"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip4, tg.layer.Udp, TEMPLATE, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--length", default=666, help="payload length; eg. 123")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		if fields["length"]:
			fields["length"] = int(fields["length"])

		fields["eth_protocol"] = "0x800"
		fields["ip4_protocol"] = "17"
		fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + fields["length"]
		fields["ip4_total_length"] = tg.layer.Ip4.HEADER_LENGTH + fields["udp_total_length"]
		return fields



#====================================================================
@tg.modreg.register
class Udp6RandomPayload(object):
	"""generator impl - udp random payload over ipv6"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip6, tg.layer.Udp, TEMPLATE, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--length", default=666, help="payload length; eg. 123")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		if fields["length"]:
			fields["length"] = int(fields["length"])

		fields["eth_protocol"] = "0x86dd"
		fields["ip6_next_header"] = 17
		fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + fields["length"]
		fields["ip6_payload_length"] = fields["udp_total_length"]
		return fields



#====================================================================
@tg.modreg.register
class TcpHeader(object):
	"""generator impl - tcp header"""

	TEMPLATE = ""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip4, tg.layer.Tcp, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		fields["eth_protocol"] = "0x800"
		fields["ip4_protocol"] = "6"
		fields["ip4_total_length"] = tg.layer.Ip4.HEADER_LENGTH + tg.layer.Tcp.HEADER_LENGTH
		return fields



#====================================================================
@tg.modreg.register
class Tcp6Header(object):
	"""generator impl - tcp header over ipv6"""

	TEMPLATE = ""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip6, tg.layer.Tcp, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		fields["eth_protocol"] = "0x86dd"
		fields["ip6_next_header"] = 6
		fields["ip6_payload_length"] = tg.layer.Tcp.HEADER_LENGTH
		return fields



#====================================================================
@tg.modreg.register
class IcmpEcho(object):
	"""generator impl - icmp echo"""

	TEMPLATE = """
/* icmp echo data */		"{icmpecho_data}",
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip4, tg.layer.IcmpEcho, TEMPLATE, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--icmpecho_data", default="this is a ping", help="eg. data")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		def process_icmpecho_data(fields, selector):
			"""validate field"""

			if (len(fields[selector]) % 2) != 0:
				# naive (no automatic padding) csumicmp/csumip/calc_csum impl, requires data to by 16b aligned
				raise ValueError("invalid data (alignment error)")
			return fields

		fields["eth_protocol"] = "0x800"
		fields["ip4_protocol"] = 1
		fields = process_icmpecho_data(fields, "icmpecho_data")
		fields["ip4_total_length"] = tg.layer.Ip4.HEADER_LENGTH + tg.layer.IcmpEcho.HEADER_LENGTH + len(fields["icmpecho_data"])
		fields["icmpecho_payload_end"] = tg.layer.Ethernet.HEADER_LENGTH + tg.layer.Ip4.HEADER_LENGTH + 8 + len(fields["icmpecho_data"])
		return fields



#====================================================================
@tg.modreg.register
class Icmp6Echo(object):
	"""generator impl - icmp6 echo"""

	TEMPLATE = """
/* icmp6 echo data */		"{icmp6echo_data}",
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip6, tg.layer.Icmp6Echo, TEMPLATE, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--icmp6echo_data", default="this is a ping", help="eg. data")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		fields["eth_protocol"] = "0x86dd"
		fields["ip6_next_header"] = 58
		fields["ip6_payload_length"] = tg.layer.Icmp6Echo.HEADER_LENGTH + len(fields["icmp6echo_data"])
		return fields
