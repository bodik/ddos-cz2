#!/usr/bin/env python3

import argparse
import asyncio
import autobahn.asyncio.component
import autobahn.wamp.types
import json
import jsonschema
import logging
import netstat
import os
import time
import txaio
import signal
import sys
import threading
import uuid


class CommunicatorThread(threading.Thread):

	## object and thread management
	def __init__(self, url, realm, msg_schema):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "communicator"
		self.log = logging.getLogger()

		# autobahn
		self.loop = None
		self.session = None
		self.component = autobahn.asyncio.component.Component(transports=[{"url": url}], realm=realm)
		self.component.on("connect", self.sessionOnConnect)
		self.component.on("join", self.sessionOnJoin)
		self.component.on("ready", self.sessionOnReady)
		self.component.on("leave", self.sessionOnLeave)
		self.component.on("disconnect", self.sessionOnDisconnect)

		# communicator
		with open(msg_schema, "r") as ftmp:
			self.msg_schema = json.loads(ftmp.read())
		self.received = 0


	def run(self):
		self.log.info("%s begin", self.name)

		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)
		txaio.config.loop = self.loop

		self.component.start()
		try:
			self.loop.run_forever()
		except asyncio.CancelledError:
			pass

		self.loop.stop()
		self.loop.close()

		self.log.info("%s end", self.name)


	def teardown_real(self):
		"""should end the component from within communicator's thread"""

		self.log.debug("%s teardown_real begin", self.name)

		@asyncio.coroutine
		def exit():
			return self.loop.stop()

		try:
			self.component.stop()
		except Exception as e:
			self.log.error(e)

		for task in asyncio.Task.all_tasks():
			self.log.info("canceling: %s", task)
			task.cancel()
		asyncio.ensure_future(exit())

		self.log.debug("%s teardown_real end", self.name)


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.log.debug("%s teardown begin", self.name)
		self.loop.call_soon_threadsafe(self.teardown_real)
		self.log.debug("%s teardown end", self.name)


	## applicationSession / component listeners
	def sessionOnConnect(self, session, protocol):
		self.log.debug("%s: connected %s %s", self.name, session, protocol)


	def sessionOnJoin(self, session, details):
		self.log.debug("%s: joined %s %s", self.name, session, details)
		self.session = session

		self.session.subscribe(self.receiveMessage, "ddos-cz2.slaves", options=autobahn.wamp.types.SubscribeOptions(details=True))


	def sessionOnReady(self, session):
		self.log.debug("%s: ready %s", self.name, session)


	def sessionOnLeave(self, session, details):
		self.log.debug("%s: left %s %s", self.name, session, details)
		self.session = None


	def sessionOnDisconnect(self, session, was_clean):
		self.log.debug("%s: disconnected %s %s", self.name, session, was_clean)


	def receiveMessage(self, msg, details=None):
		try:
			jsonschema.validate(msg, self.msg_schema)
		except jsonschema.exceptions.ValidationError:
			self.log.warn("%s: invalid message %s %s", self.name, msg, details)
			return

		self.log.info("%s: message %s %s", self.name, msg, details)
		self.received += 1
		if self.received > 2:
			try:
				self.teardown_real()
			except Exception as e:
				self.log.error(e)





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
	if args.debug:
		logger.setLevel(logging.DEBUG)
	logger.handlers = []
	txaio.start_logging(level=logging.getLevelName(logger.getEffectiveLevel()).lower())


	# startup
	signal.signal(signal.SIGTERM, teardown)
	signal.signal(signal.SIGINT, teardown)
	thread_communicator = CommunicatorThread(args.server, args.realm, args.schema)
	thread_communicator.start()

	# there will be a loop

	thread_communicator.join()


if __name__ == "__main__":
	sys.exit(main())
