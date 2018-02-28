"""base generator class"""

import logging
import netifaces
import subprocess
import tempfile


class BaseGenerator(object):
	"""base generator, holds code to execute the generator"""

	IP_HEADER_LENGTH = 20
	UDP_HEADER_LENGTH = 8



	@classmethod
	def parse_arguments(cls, parser):
		parser.add_argument("--dev",
			help="output network interface")

		parser.add_argument("--ip_ttl", default=21)
		parser.add_argument("--ip_source_address")
		parser.add_argument("--ip_destination_address")



	def __init__(self, fields):
		self.log = logging.getLogger()
		self.fields = fields



	def generate_config(self):
		return self.TRAFGEN_CONFIG.format(**self.fields)



	def execute(self):
		pass
