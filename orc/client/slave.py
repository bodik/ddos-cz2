#!/usr/bin/env python3

import argparse
import communicator
import logging
import netstat
import os
import txaio
import signal
import sys
import threading
import uuid



class NetstatThread(threading.Thread):

	def __init__(self, communicator):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "netstater"
		self.log = logging.getLogger()

		self.communicator = communicator
		self.shutdown = False
		self.interface = "eth0"
		self.timespan = 1


	def run(self):
		self.log.info("thread %s begin", self.name)

		while not self.shutdown:
			obj = {"Id": str(uuid.uuid4()), "Type": "netstat", "Message": {"data": netstat.stats(self.interface, self.timespan)}}
			self.communicator.sendMessage(obj)

		self.log.info("thread %s end", self.name)


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.log.debug("%s teardown begin", self.name)
		self.shutdown = True
		self.log.debug("%s teardown end", self.name)



def handle_message(msg):
	print(msg)



def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
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

	thread_communicator = communicator.CommunicatorThread(args.server, args.realm, args.schema, handle_message)
	thread_communicator.start()

	thread_netstat = NetstatThread(thread_communicator)
	thread_netstat.start()

	thread_netstat.join()
	thread_communicator.join()



if __name__ == "__main__":
	sys.exit(main())
