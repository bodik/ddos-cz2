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
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ipv4, tg.layer.Udp, TEMPLATE, "}}"]

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
		fields["ip_protocol"] = "17"
		fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + fields["length"]
		fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + fields["udp_total_length"]
		return fields



#====================================================================
@tg.modreg.register
class Udp6RandomPayload(object):
	"""generator impl - udp random payload over ipv6"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ipv6, tg.layer.Udp, TEMPLATE, "}}"]

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
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ipv4, tg.layer.Tcp, "}}"]

	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		fields["eth_protocol"] = "0x800"
		fields["ip_protocol"] = "6"
		fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + tg.layer.Tcp.HEADER_LENGTH
		return fields
