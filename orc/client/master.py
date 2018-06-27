#!/usr/bin/env python3
"""master orc"""


import argparse
import communicator
import logging
import shlex
import socket
import sys
import time
import txaio
import ui


class MasterShell(object):
	"""master shell object"""

	## object and thread management
	def __init__(self):
		self.name = "mastershell"
		self.log = logging.getLogger()

		self.communicator = None
		self.console = None
		self.shutdown = False


	def run(self, args):
		"""main"""

		self.log.debug("%s thread begin", self.name)
		self.communicator = communicator.CommunicatorThread(args.server, args.realm, args.schema, args.identity, self.handle_message)
		self.communicator.start()

		if args.ui == "formed":
			self.console = ui.Formed(self.handle_command)

		if args.ui == "listener":
			self.console = ui.Listener()

		if args.ui == "commander":
			self.console = ui.Commander(self.handle_command)
			timeout = 10
			while (not self.communicator.session) and (timeout > 0):
				self.log.info("waiting on session")
				timeout -= 1
				time.sleep(1)

		try:
			self.console.run()
		except KeyboardInterrupt:
			pass

		self.communicator.teardown()
		self.communicator.join()
		self.log.debug("%s thread end", self.name)


	def teardown(self):
		"""teardown component"""
		pass


	## application interface
	def handle_message(self, message):
		"""handle incomming messages, communicator's callback"""

		self.console.handle_message(message)


	def handle_command(self, command):
		"""reply to application ping"""

		cmd = shlex.split(command)
		self.communicator.send_message({"Type": "command", "Message": {"command": cmd[0], "arguments": cmd[1:]}})


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
	parser.add_argument("--identity", default=socket.getfqdn())
	parser.add_argument("--ui", default="formed", choices=["formed", "listener", "commander"])
	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()



def main():
	"""main"""

	# args
	args = parse_arguments()

	# txaio startup messes up standard logging
	logger = logging.getLogger()
	logger.handlers = []
	logger.setLevel(logging.INFO)
	txaio.start_logging(level="info")
	if args.debug:
		logger.setLevel(logging.DEBUG)
		txaio.start_logging(level="debug")

	# startup
	MasterShell().run(args)



if __name__ == "__main__":
	sys.exit(main())
