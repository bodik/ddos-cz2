#!/usr/bin/python
"""generators implementation"""

import tg


#====================================================================
@tg.modreg.register
class EthernetFilePayload(object):
	"""generator impl - udp random payload"""

	TEMPLATE = """
/* payload */				{payload}
"""
	LAYERS = [tg.layer.Ethernet, TEMPLATE]
	
	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""
	
		parser.add_argument("--eth_protocol", required=True ,help="eg. 0x0800")
		parser.add_argument("--filename", required=True, help="full payload filename")


	@staticmethod
	def process_fields(fields):
		with open(fields["filename"], "r") as ftmp:
			fields["payload"] = ftmp.read()
		return fields
	


#====================================================================
@tg.modreg.register
class UdpRandomPayload(object):
	"""generator impl - udp random payload"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = [tg.layer.Ethernet, tg.layer.Ipv4, tg.layer.Udp, TEMPLATE]

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
