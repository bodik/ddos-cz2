#!/usr/bin/python
"""generators implementation"""

import tg



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

		fields["eth_protocol"] = "0x800"
		fields["ip_protocol"] = "17"
		fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + fields["length"]
		fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + fields["udp_total_length"]
		return fields
