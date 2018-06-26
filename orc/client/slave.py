#!/usr/bin/env python3

import argparse
import communicator
import logging
import netstat
import txaio
import signal
import socket
import sys
import threading



class NetstatThread(threading.Thread):

	## object and thread management
	def __init__(self, communicator, interface="eth0", timespan=1):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "netstat"
		self.log = logging.getLogger()

		self.communicator = communicator
		self.interface = interface
		self.timespan = timespan
		self.shutdown = False


	def run(self):
		self.log.info("%s thread begin", self.name)

		while not self.shutdown:
			obj = {"Type": "netstat", "Message": netstat.stats(self.interface, self.timespan)}
			self.communicator.sendMessage(obj)

		self.log.info("%s thread end", self.name)


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.shutdown = True



class SlaveShell():
	"""slave shell object"""

	## object and thread management
	def __init__(self):
		self.name = "slaveshell"
		self.log = logging.getLogger()

		self.communicator = None


	def run(self, args):
		self.log.info("%s thread begin", self.name)

		self.communicator = communicator.CommunicatorThread(args.server, args.realm, args.schema, args.identity, self.handle_message)
		self.communicator.start()
		self.communicator.join()

		self.log.info("%s thread end", self.name)

	def teardown(self):
		self.communicator.teardown()


	## appllication interface
	def handle_message(self, msg):
		self.log.debug("%s handle_message %s", self.name, msg)

		if msg["Type"] == "command":
			try:
				command_callable = "command_%s" % msg["Message"]["command"]
				if hasattr(self, command_callable) and callable(getattr(self, command_callable)):
					call = getattr(self, command_callable)
					call(msg["Message"]["arguments"])
			except Exception as e:
				self.log.error("%s invalid command %s %s", self.name, msg, e)


	def command_tlist(self, arguments):
		data = [{"name": thread.name, "ident": thread.ident} for thread in threading.enumerate()]
		self.communicator.sendMessage({"Type": "tlist", "Message": data})


	def command_tstop(self, arguments):
		for thread in threading.enumerate():
			if str(thread.ident) in arguments:
				thread.teardown()
				thread.join(10)


	def command_netstat(self, arguments):
		self.log.info("command_netstat %s", arguments)
		if "off" in arguments:
			for thread in threading.enumerate():
				if thread.name == "netstat":
					thread.teardown()
					thread.join(10)
		else:
			thread = NetstatThread(self.communicator)
			thread.start()



def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
	parser.add_argument("--identity", default=socket.getfqdn())
	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()


def teardown(signum, frame):
	logger = logging.getLogger()
	logger.info("signaled teardown begin")

	# shutdown all running threads without passing references through global variables
	for thread in threading.enumerate():
		if hasattr(thread, "teardown") and callable(getattr(thread, "teardown")):
			thread.teardown()
			thread.join(10)

	logger.info("signaled teardown end")


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
	signal.signal(signal.SIGTERM, teardown)
	signal.signal(signal.SIGINT, teardown)
	SlaveShell().run(args)



if __name__ == "__main__":
	sys.exit(main())
