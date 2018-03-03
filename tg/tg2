#!/usr/bin/python

import argparse
import logging
import sys
import tg

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser_commands = parser.add_subparsers(dest="command")
	for cls in tg.modreg.registered_classes:
		parser_command = parser_commands.add_parser(cls.__name__)
		cls.parse_arguments(parser_command)

	return parser.parse_args()



def main():
	
	# parse cmdline
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)


	# setup
	generator = getattr(tg, args.command)(args.__dict__)
	logger.debug("generator fields: %s", generator.fields)

	if args.dump:
		print generator.config()
	else:
		generator.execute()



if __name__ == "__main__":
	sys.exit(main())
