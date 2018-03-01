"""base generator class"""

import logging
import os
import subprocess
import sys
import tempfile
import tg


class BaseGenerator(object):
	"""base generator, holds code to execute the generator"""

	IP_HEADER_LENGTH = 20
	UDP_HEADER_LENGTH = 8



	@classmethod
	def parse_arguments(cls, parser):
		# common arguments
		parser.add_argument("--num", default=100, \
			help="number of packets to send")
		parser.add_argument("--gap", default=0, \
			help="interpacket gap")

		# l2 arguments
		parser.add_argument("--dev", \
			help="output network interface")
		parser.add_argument("--eth_source_mac", \
			help="ethernet frame source mac address")
		parser.add_argument("--eth_destination_mac", \
			help="ethernet frame destination mac address")

		# l3 arguments
		parser.add_argument("--ip_ttl", default=21)
		parser.add_argument("--ip_source_address", default="self", \
			help="ip source addres -- a.b.c.d|self|rnd|drnd")
		parser.add_argument("--ip_destination_address", default="self", \
			help="ip destination addres -- a.b.c.d|self|rnd|drnd")



	def __init__(self, fields):
		self.log = logging.getLogger()
		self.fields = fields


	def process_fields(self):
		# select output interface
		if not self.fields["dev"]:
			self.fields["dev"] = tg.utils.default_output_interface()


		## resolve mac addresses
		if not self.fields["eth_source_mac"]:
			self.fields["eth_source_mac"] = tg.utils.interface_mac(self.fields["dev"])
		self.fields["eth_source_mac"] = tg.utils.trafgen_format_mac(self.fields["eth_source_mac"])

		if not self.fields["eth_destination_mac"]:
			self.fields["eth_destination_mac"] = tg.utils.ip_to_mac(tg.utils.interface_gateway_ip(self.fields["dev"]), self.fields["dev"])
		self.fields["eth_destination_mac"] = tg.utils.trafgen_format_mac(self.fields["eth_destination_mac"])


		## preprocess ip addresses
		if self.fields["ip_source_address"] == "self":
			self.fields["ip_source_address"] = tg.utils.interface_ip(self.fields["dev"])
		elif self.fields["ip_source_address"] in ["rnd", "drnd"]:
			address = tg.utils.interface_ip(self.fields["dev"]).split(".")
			address[-1] = "%s(1)" % self.fields["ip_source_address"]
			self.fields["ip_source_address"] = ".".join(address)
		self.fields["ip_source_address"] = tg.utils.trafgen_format_ip(self.fields["ip_source_address"])

		if self.fields["ip_destination_address"] == "self":
			self.fields["ip_destination_address"] = tg.utils.interface_ip(self.fields["dev"])
		elif self.fields["ip_destination_address"] in ["rnd", "drnd"]:
			address = tg.utils.interface_ip(self.fields["dev"]).split(".")
			address[-1] = "%s(1)" % self.fields["ip_destination_address"]
			self.fields["ip_destination_address"] = ".".join(address)
		self.fields["ip_destination_address"] = tg.utils.trafgen_format_ip(self.fields["ip_destination_address"])
		


	def generate_config(self):
		return self.TRAFGEN_CONFIG.format(**self.fields)



	def execute(self):
		ftmp = tempfile.NamedTemporaryFile(prefix="tg_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.generate_config())
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
