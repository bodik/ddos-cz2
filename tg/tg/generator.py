#!/usr/bin/python
"""generators implementation"""


import logging
import os
import subprocess
import sys
import tempfile
import tg



#====================================================================
class Base(object):
	"""base generator, holds code to execute the generator"""

	LAYERS = []
	TEMPLATE = ""

	WRAPPER = """
#include "{tg_path}/bin/trafgen_stddef.h"
{{{{
{packet}
}}}}
"""

	@classmethod
	def build_arguments_parser(cls, parser):
		"""parse common arguments, add all layers parsers, impl specific arguments"""

		parser.add_argument("--debug", action="store_true", default=False, help="debug output")
		parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")
		parser.add_argument("--num", default=100, help="number of packets to send")
		parser.add_argument("--gap", default=0,	help="interpacket gap")

		for layer in [x for x in cls.LAYERS if isinstance(x, type)]:
			layer.parse_arguments(parser)

		cls.parse_arguments(parser)



	@staticmethod
	def parse_arguments(parser):
		"""parse arguments abstract placeholder"""
		pass



	@staticmethod
	def process_fields(fields):
		"""process fields abstract placeholder"""
		return fields



	def __init__(self, fields):
		"""initialize fields, run all layers postprocessors, impl specific postprocessing"""

		self.fields = fields
		for layer in [x for x in self.LAYERS if isinstance(x, type)]:
			self.fields = layer.process_fields(self.fields)
		self.fields = self.__class__.process_fields(self.fields)



	def compile(self):
		"""compile source for trafgen"""

		# compile source for config from all layers
		template = ""
		for layer in self.LAYERS:
			if isinstance(layer, type):
				template += layer.TEMPLATE
			else:
				template += layer

		# wrap and fill fields
		wrapped = tg.generator.Base.WRAPPER.format( \
			tg_path=os.path.dirname(os.path.realpath(sys.argv[0])),
			packet=template)
		return wrapped.format(**self.fields)



	def execute(self):
		"""run trafgen"""

		# write config to filesystem
		ftmp = tempfile.NamedTemporaryFile(prefix="tg_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.compile())
		ftmp.close()

		# run trafgen
		trafgen_bin = "%s/bin/trafgen" % os.path.dirname(os.path.realpath(sys.argv[0]))
		cmd = [trafgen_bin, "--in", ftmp_name, "--out", self.fields["dev"], "--num", str(self.fields["num"]), "--gap", str(self.fields["gap"]), "--cpp"]
		logging.debug(cmd)
		try:
			logging.debug(subprocess.check_output(cmd))
		except Exception as e:
			logging.error(e)
			return

		# cleanup
		os.unlink(ftmp_name)






#====================================================================
@tg.modreg.register
class UdpRandomPayload(Base):
	"""generator impl - udp random payload"""

	TEMPLATE = """
/* payload */				drnd({length}),
"""
	LAYERS = [tg.layer.Ethernet, tg.layer.Ipv4, tg.layer.Udp, TEMPLATE]

	@staticmethod
	def parse_arguments(parser):
		parser.add_argument("--length", default=666, help="payload length; eg. 123")


	@staticmethod
	def process_fields(fields):
		fields["eth_protocol"] = "0x800"
		fields["ip_protocol"] = "17"
		fields["udp_total_length"] = tg.layer.Udp.HEADER_LENGTH + fields["length"]
		fields["ip_total_length"] = tg.layer.Ipv4.HEADER_LENGTH + fields["udp_total_length"]
		return fields
