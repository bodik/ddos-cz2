#!/usr/bin/python

import argparse
import logging
import netifaces
import sys
import tg

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", action="store_true", default=False, help="debug output")

	tg.generator.base.BaseGenerator.parse_arguments(parser)

	parser_command = parser.add_subparsers(dest="command")
	for cls in tg.generator.modreg.registered_classes:
		cls.parse_arguments(parser_command)


	return parser.parse_args()


def main():
	
	# parse cmdline
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)
	logger.debug(args)


	# setup
	fields = args.__dict__


	# default output interface is one with default gateway
	# TODO: IPv6
	if not fields["dev"]:
		fields["dev"] = netifaces.gateways()["default"][netifaces.AF_INET][1]
	fields["eth_source_mac"] = netifaces.ifaddresses(fields["dev"])[netifaces.AF_LINK][0]["addr"]
	router_address = netifaces.gateways()["default"][netifaces.AF_INET][1]
	fields["eth_destination_mac"] 


	logger.debug(fields)




	# execute
	generator = getattr(tg, args.command)(fields)
	logger.debug(generator.generate_config())

	
	# cleanup
	#TODO: cleanup




if __name__ == "__main__":
	sys.exit(main())
