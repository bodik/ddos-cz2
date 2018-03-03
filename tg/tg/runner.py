#!/usr/bin/python
"""runner module"""

import logging
import os
import subprocess
import sys
import tempfile
import tg



class Runner(object):
	"""executor holds code to execute the generator"""

	WRAPPER = """
#include "{tg_path}/bin/trafgen_stddef.h"
{{{{
{packet}
}}}}
"""

	@staticmethod
	def build_arguments_parser(parser, generator):
		"""parse common arguments, add all layers parsers, generator specific arguments"""

		parser.add_argument("--debug", action="store_true", default=False, help="debug output")
		parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")
		parser.add_argument("--num", default=100, help="number of packets to send")
		parser.add_argument("--gap", default=0,	help="interpacket gap")

		for layer in [x for x in generator.LAYERS if isinstance(x, type)]:
			layer.parse_arguments(parser)
		generator.parse_arguments(parser)



	def __init__(self, generator, fields):
		"""initialize fields, run all layers postprocessors, generator specific postprocessing"""

		self.generator = generator
		self.fields = fields
		for layer in [x for x in self.generator.LAYERS if isinstance(x, type)]:
			self.fields = layer.process_fields(self.fields)
		self.fields = self.generator.process_fields(self.fields)



	def compile(self):
		"""compile source for trafgen"""

		# compile source for config from all layers
		template = ""
		for layer in self.generator.LAYERS:
			if isinstance(layer, type):
				template += layer.TEMPLATE
			else:
				template += layer

		# wrap and fill fields
		wrapped = tg.runner.Runner.WRAPPER.format( \
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
