"""generators implementation"""

import tg


#====================================================================
@tg.modreg.register
class RawConfig():
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
class UdpStaticPayload():
	"""generator impl - udp static payload"""

	TEMPLATE = """
/* payload */                           fill(0x41, {length})
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
class UdpRandomPayload(UdpStaticPayload):
	"""generator impl - udp random payload"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip4, tg.layer.Udp, TEMPLATE, "}}"]



#====================================================================
@tg.modreg.register
class Udp6RandomPayload():
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
class TcpHeader():
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
class Tcp6Header():
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
class IcmpEcho():
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
class Icmp6Echo():
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



#====================================================================
@tg.modreg.register
class DnsQueryUdpPayload(UdpStaticPayload):
	"""generator impl - dns query udp payload"""

	TEMPLATE = """
/* dns txid */				drnd(2),
/* dns flags */				0x01, 0x00,

/* dns number of questions */		c16(1),
/* dns answer rr */			c16(0),
/* dns auth rr */			c16(0),
/* dns add rr */			c16({dns_additional_records}),

/* dns query encoded data */		{dns_query_data}
/* dns query type (any) */		0x00, {dns_query_type},
/* dns query class (in) */		c16(1),

/* dns additional records */		{dns_additional_records_data}
"""
	LAYERS = ["{{", tg.layer.Ethernet, tg.layer.Ip4, tg.layer.Udp, TEMPLATE, "}}"]


	@staticmethod
	def parse_arguments(parser):
		"""parse arguments"""

		parser.add_argument("--dns_query_name", default="test", help="name to query; eg. domain.ex")
		parser.add_argument("--dns_query_type", default="any", help="query type; eg. any, txt, ...")
		parser.add_argument("--dns_nolarge", action="store_true", help="request large answer")


	@staticmethod
	def process_fields(fields):
		"""process arguments to fileds"""

		def process_dns_query_type(fields, selector):
			"""validate field"""

			if fields[selector] == 'any':
				fields["dns_query_type"] = "0xff"
			elif fields[selector] == 'txt':
				fields["dns_query_type"] = "0x10"
			else:
				raise ValueError("invalid dns query type")
			return fields

		fields["udp_destination_port"] = 'c16(53)'
		fields = process_dns_query_type(fields, "dns_query_type")
		fields["length"] = 16

		fields["dns_query_data"] = []
		for part in fields["dns_query_name"].split('.'):
			fields["length"] += 1+len(part)
			fields["dns_query_data"] += [str(len(part)), '"%s"'%part]
		fields["length"] += 1
		fields["dns_query_data"].append('0x00')
		fields["dns_query_data"] = ",".join(fields["dns_query_data"])

		fields["dns_additional_records"] = 0
		fields["dns_additional_records_data"] = ""
		if not fields["dns_nolarge"]:
			fields["dns_additional_records"] = 1
			fields["dns_additional_records_data"] = "0x00, 0x00, 0x29, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00"
			fields["length"] += 11

		fields = super(DnsQueryUdpPayload, DnsQueryUdpPayload).process_fields(fields)
		return fields
