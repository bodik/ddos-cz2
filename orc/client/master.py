#!/usr/bin/env python3


import argparse
import communicator
import console
import logging
import random
import socket
import sys
import txaio



class MasterShell(object):
	"""master shell object"""

	## object and thread management
	def __init__(self):
		self.name = "mastershell"
		self.log = logging.getLogger()

		self.communicator = None
		self.shutdown = False


	def run(self, args):
		self.log.info("%s thread begin", self.name)

		identity = socket.getfqdn()
		self.communicator = communicator.CommunicatorThread(args.server, args.realm, args.schema, identity, self.handle_message)
		self.communicator.start()

		self.console = console.Console()

		while not self.shutdown:
			try:
				prompt_input = self.console.prompt_input()
				self.handle_command(prompt_input.strip())
			except KeyboardInterrupt:
				self.shutdown = True
			except Exception as e:
				self.shutdown = True
				self.console.teardown()
				self.log.error(e)

		self.console.teardown()

		self.communicator.teardown()
		self.communicator.join()

		self.log.info("%s thread end", self.name)


	def teardown(self):
		pass


	## application interface
	def handle_message(self, msg):
		self.console.add_line("[%s] %s: %s" % (msg["Node"], msg["Id"], msg["Message"]))

	def handle_command(self, command):
		cmd = command.split(" ")
	
		if cmd[0] == "quit":
			self.shutdown = True
		
		if cmd[0] in ["netstat", "tlist", "tstop"]:
			self.communicator.sendMessage({"Type": "command", "Message": {"command": cmd[0], "arguments": cmd[1:]}})


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
	parser.add_argument("--identity", default=socket.getfqdn())
	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()



def main():
	"""main"""

	# args
	args = parse_arguments()

	# txaio startup messes up standard logging
	logger = logging.getLogger()
	logger.handlers = []
	logger.setLevel(logging.WARNING)
	txaio.start_logging(level="warn")
	if args.debug:
		logger.setLevel(logging.DEBUG)
		txaio.start_logging(level="debug")

	# startup
	MasterShell().run(args)



if __name__ == "__main__":
	sys.exit(main())
