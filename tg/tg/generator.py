#!/usr/bin/python

import logging
import os
import subprocess
import sys
import tempfile
import tg.modreg



class Base(object):
	"""base generator, holds code to execute the generator"""

	CONFIG = """
#include "trafgen_stddef.h"
{{
{packet}
}}
"""

	@staticmethod
	def parse_arguments(parser):
		parser.add_argument("--debug", action="store_true", default=False, help="debug output")
		parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")
		parser.add_argument("--num", default=100, help="number of packets to send")
		parser.add_argument("--gap", default=0,	help="interpacket gap")

	@staticmethod
	def process_fields(fields):
		return fields



	def __init__(self, fields):
		self.fields = fields


	def execute(self):
		ftmp = tempfile.NamedTemporaryFile(prefix="tg_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.config())
		ftmp.close()

		trafgen_bin = "%s/bin/trafgen" % os.path.dirname(os.path.realpath(sys.argv[0]))
		cmd = [trafgen_bin, "--in", ftmp_name, "--out", self.fields["dev"], "--num", str(self.fields["num"]), "--gap", str(self.fields["gap"]), "--cpp"]
		logging.debug(cmd)
		try:
			subprocess.check_call(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except Exception as e:
			logging.error(e)
			return

		os.unlink(ftmp_name)






@tg.modreg.register
class UdpRandomPayload(Base):
	"""generator impl - udp random payload"""

	CONFIG = """
/* payload */				drnd({length}),
"""

	@staticmethod
	def parse_arguments(parser):
		tg.generator.Base.parse_arguments(parser)
		tg.layer.Ethernet.parse_arguments(parser)
		tg.layer.Ipv4.parse_arguments(parser)
		tg.layer.Udp.parse_arguments(parser)

		parser.add_argument("--length", default=666, help="payload length; eg. 123")



	def __init__(self, fields):
		tg.generator.Base.__init__(self, fields)

		self.fields = tg.generator.Base.process_fields(self.fields)
		self.fields = tg.layer.Ethernet.process_fields(self.fields)
		self.fields = tg.layer.Ipv4.process_fields(self.fields)
		self.fields = tg.layer.Udp.process_fields(self.fields)

		self.fields["eth_protocol"] = "0x800"
		self.fields["ip_protocol"] = "17"
		self.fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + self.fields["length"]
		self.fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + self.fields["udp_total_length"]


	def config(self):
		layers = [tg.layer.Ethernet.CONFIG, tg.layer.Ipv4.CONFIG, tg.layer.Udp.CONFIG, self.CONFIG]
		packet = "".join(layers).format(**self.fields)
		return tg.generator.Base.CONFIG.format(packet=packet)
