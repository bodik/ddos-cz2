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
	parser.add_argument("--debug", action="store_true", default=False, help="debug output")
	parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")

	tg.generator.base.BaseGenerator.parse_arguments(parser)

	parser_command = parser.add_subparsers(dest="command")
	for cls in tg.modreg.registered_classes:
		cls.parse_arguments(parser_command)


	return parser.parse_args()



def main():
	
	# parse cmdline
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)
	#logger.debug("starup args: %s", args)


	# setup
	generator = getattr(tg, args.command)(args.__dict__)
	generator.process_fields()
	logger.debug("generator fields: %s", generator.fields)

	if args.dump:
		print generator.generate_config()
	else:
		generator.execute()


	
	# cleanup
	#TODO: cleanup




if __name__ == "__main__":
	sys.exit(main())
