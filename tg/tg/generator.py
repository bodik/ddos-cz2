#!/usr/bin/python

import logging
import os
import subprocess
import sys
import tempfile
import tg



#====================================================================
class Base(object):
	"""base generator, holds code to execute the generator"""

	PACKET_WRAPPER = """
#include "trafgen_stddef.h"
{{{{
{packet}
}}}}
"""

	@classmethod
	def parse_arguments(cls, parser):
		"""parse arguments and add all layers parsers"""

		# generator common parameters
		parser.add_argument("--debug", action="store_true", default=False, help="debug output")
		parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")
		parser.add_argument("--num", default=100, help="number of packets to send")
		parser.add_argument("--gap", default=0,	help="interpacket gap")

		# incorporate all arguments from generator's impl layers
		for layer in [x for x in cls.LAYERS if type(x) == type]:
			layer.parse_arguments(parser)



	def __init__(self, fields):
		"""initialize all fields, postprocess them, run all layers postprocessors"""

		# generator common fields
		self.fields = fields

		# postprocess fields by all generator's impl layers
		for layer in [x for x in self.LAYERS if type(x) == type]:
			self.fields = layer.process_fields(fields)



	def config(self):
		"""compile source for config"""

		# compile source for config from all layers
		source = ""
		for layer in self.LAYERS:
			if type(layer) == type:
				source += layer.CONFIG
			else:
				source += layer

		# wrap and fill fields
		return tg.generator.Base.PACKET_WRAPPER.format(packet=source).format(**self.fields)



	def execute(self):
		# write config to filesystem
		ftmp = tempfile.NamedTemporaryFile(prefix="tg_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.config())
		ftmp.close()

		# run trafgen
		trafgen_bin = "%s/bin/trafgen" % os.path.dirname(os.path.realpath(sys.argv[0]))
		cmd = [trafgen_bin, "--in", ftmp_name, "--out", self.fields["dev"], "--num", str(self.fields["num"]), "--gap", str(self.fields["gap"]), "--cpp"]
		logging.debug(cmd)
		try:
			subprocess.check_call(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except Exception as e:
			logging.error(e)
			return

		# cleanup
		os.unlink(ftmp_name)






#====================================================================
@tg.modreg.register
class UdpRandomPayload(Base):
	"""generator impl - udp random payload"""

	CONFIG = """
/* payload */				drnd({length}),
"""
	LAYERS = [tg.layer.Ethernet, tg.layer.Ipv4, tg.layer.Udp, CONFIG]

	@classmethod
	def parse_arguments(cls, parser):
		super(cls, cls).parse_arguments(parser)
		parser.add_argument("--length", default=666, help="payload length; eg. 123")



	def __init__(self, fields):
		super(self.__class__, self).__init__(fields)

		self.fields["eth_protocol"] = "0x800"
		self.fields["ip_protocol"] = "17"
		self.fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + self.fields["length"]
		self.fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + self.fields["udp_total_length"]
