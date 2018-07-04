#!/usr/bin/python3
"""print node description"""

import argparse
import json
import logging
import shlex
import subprocess
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')
logger = logging.getLogger()
sys.tracebacklimit = None


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--iface", default="eth0")
	return parser.parse_args()


def main():
	"""main"""

	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)


	facts = json.loads(subprocess.check_output(shlex.split("facter --json")).decode("UTF-8"))

	try:
		pciid = list(filter( \
			lambda x: x.startswith("E: ID_PATH=pci-"),
			subprocess.check_output( \
				shlex.split("udevadm info --path /sys/class/net/%s" % args.iface),
				stderr=subprocess.DEVNULL).decode("UTF-8").splitlines()))[0].split("-")[1]
		logger.debug("iface pciid: %s", pciid)

		ifaceinfo = ("%s="%args.iface) + ";".join(filter( \
			lambda x: x.startswith("%s " % pciid),
			subprocess.check_output(shlex.split("lspci -D"), stderr=subprocess.DEVNULL).decode("UTF-8").splitlines()))
		logger.debug("pciinfo: %s", ifaceinfo)
	except Exception as e:
		logger.error(e)
		ifaceinfo = None


	node_description = { \
		"fqdn": facts["fqdn"],
		"iface": ifaceinfo,
		"lsbdistdescription": facts["lsbdistdescription"],
		"memorysize": facts["memorysize"],
		"physicalprocessorcount": facts["physicalprocessorcount"],
		"processorcount": facts["processorcount"],
		"processor0": facts["processor0"],
		"uname": subprocess.check_output(["uname", "-a"]).decode("UTF-8"),
		"virtual": facts["virtual"]}
	print(json.dumps(node_description, indent=4, sort_keys=True))



if __name__ == "__main__":
	main()
