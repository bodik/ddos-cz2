"""module udp_random_payload"""

import tg


@tg.modreg.register
class UdpRandomPayload(tg.generator.base.BaseGenerator):
	"""generator impl - udp random payload"""

	TRAFGEN_CONFIG = """
#include "trafgen_stddef.h"
{{
	/* header ethernet */
	{eth_destination_mac},		/* Destination MAC */
	{eth_source_mac},		/* Source MAC */
	c16(ETH_P_IP),			/* IPv4 Protocol */

	/* header ip */
	0b01000101, 0,			/* IPv4 Version, IHL, TOS */
	c16({ip_total_length}),		/* IPv4 Total Len */
	drnd(2),			/* IPv4 Ident */
	0b01000000, 0,			/* IPv4 Flags, Frag Off */
	{ip_ttl},			/* IPv4 TTL */
	IPPROTO_UDP,			/* Proto = UDP */
	IP_CSUM_DEFAULT,		/* IPv4 Checksum (IP header from, to) */
	{ip_source_address},		/* Source IP */
	{ip_destination_address},	/* Destination IP */

	/* header udp */
	{source_port},			/* Source Port */
	{destination_port},		/* Destination Port */
	const16({udp_total_length}),	/* UDP Length */
	const16(0),			/* UDP checksum (Can be zero) */

	/* payload */
	drnd({length}),
}}
"""

	@classmethod
	def parse_arguments(cls, parser):
		"""parse arguments"""

		parser_gen = parser.add_parser(cls.__name__, help="command help")

		parser_gen.add_argument("--source_port", default=12345,
			help="udp source port -- int|rnd|drnd")
		parser_gen.add_argument("--destination_port", default=12345,
			help="udp destination port -- int|rnd|drnd")
		parser_gen.add_argument("--length", default=666,
			help="udp payload length")



	def __init__(self, args):
		tg.generator.base.BaseGenerator.__init__(self, args)

		self.fields["udp_total_length"] = self.UDP_HEADER_LENGTH + self.fields["length"]
		self.fields["ip_total_length"] = self.IP_HEADER_LENGTH + self.fields["udp_total_length"]
	


	def process_fields(self):
		tg.generator.base.BaseGenerator.process_fields(self)
	
		if self.fields["source_port"] in ["rnd", "drnd"]:
			self.fields["source_port"] = "%s(2)" % self.fields["source_port"]
		else:
			self.fields["source_port"] = "c16(%d)" % int(self.fields["source_port"])

		if self.fields["destination_port"] in ["rnd", "drnd"]:
			self.fields["destination_port"] = "%s(2)" % self.fields["destination_port"]
		else:
			self.fields["destination_port"] = "c16(%d)" % int(self.fields["destination_port"])


