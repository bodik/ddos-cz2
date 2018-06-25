#!/usr/bin/env python3


import argparse
import communicator
import logging
import random
import os
import signal
import sys
import threading
import time
import txaio
import uuid



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
	sys.exit(0)



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

	counter = 0
	while True:
		obj = {"counter": counter, "foo": [1, 2, 3]}
		thread_communicator.sendMessage(obj)
		counter += 1

		obj = {"Id": str(uuid.uuid4()), "Type": "test"}
		thread_communicator.sendMessage(obj)
		counter += 1

		time.sleep(1)

	thread_communicator.join()



if __name__ == "__main__":
	sys.exit(main())

