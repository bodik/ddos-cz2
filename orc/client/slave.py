#!/usr/bin/env python3

import argparse
import asyncio
import autobahn.asyncio.wamp
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

txaio.use_asyncio()


class CommunicatorWampSession(autobahn.asyncio.wamp.ApplicationSession):

	def __init__(self, *args, **kwargs):
		super(CommunicatorWampSession, self).__init__(*args, **kwargs)
		self.received = 0
		self.msg_schema = self.config.extra["msg_schema"]
		self.communicator_thread = self.config.extra["communicator_thread"]

	async def onJoin(self, details):
		def on_message(msg, details):
			self.processMessage(msg)

		self.log.info("{cls}: joined {details}", cls=self.__class__.__name__, details=details)
		await self.subscribe(on_message, "ddos-cz2.slaves", options=autobahn.wamp.types.SubscribeOptions(details=True))

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

	def processMessage(self, msg):
		try:
			jsonschema.validate(msg, self.msg_schema)
		except jsonschema.exceptions.ValidationError:
			self.log.warn("{cls}: invalid message {msg}", cls=self.__class__.__name__, msg=msg)
			return

		self.log.info("{cls}: message {msg}", cls=self.__class__.__name__, msg=msg)
		self.received += 1
		if self.received > 30:
			self.leave()


class CommunicatorThread(threading.Thread):
	def __init__(self, server, realm, msg_schema, log_level="info"):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "communicator"
		self.log = txaio.make_logger() #caveat: mind the semantic slightly differs from python's standard logging

		# mandatory asyncio
		self.loop = None
		self.log_level = log_level

		# comms
		self.shutdown = False
		self.server = server
		self.realm = realm
		with open(msg_schema, "r") as ftmp:
			self.msg_schema = json.loads(ftmp.read())

		# ipc
		self.inbox = []
		self.outbox = []


	def run(self):
		self.log.info("start %s" % self.name)

		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)

		self.shutdown = False
		while not self.shutdown:
			try:
				## code mainly taken from ApplicationRunner but can handle repeating router failures/disconnects
				self.loop = asyncio.get_event_loop()
				if self.loop.is_closed():
				        asyncio.set_event_loop(asyncio.new_event_loop())
				        self.loop = asyncio.get_event_loop()
				runner = autobahn.asyncio.wamp.ApplicationRunner(self.server, realm=self.realm, extra={"communicator_thread": self, "msg_schema": self.msg_schema})
				coro = runner.run(CommunicatorWampSession, start_loop=False, log_level=self.log_level)
				(transport, protocol) = self.loop.run_until_complete(coro)
				## must not be handled by thread but only by main itself
				###self.loop.add_signal_handler(signal.SIGTERM, self.loop.stop)
				try:
				        self.loop.run_forever()
				except KeyboardInterrupt:
				        self.log.info("aborted by user")
				        self.shutdown = True
				if protocol._session:
				        self.loop.run_until_complete(protocol._session.leave())
				self.loop.close()

			except Exception as e:
				self.log.error(e)
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					self.shutdown = True

		self.log.info("end %s" % self.name)

	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.log.info("shutting down %s" % self.name)
		self.shutdown = True
		self.loop.stop()


	def send(self, msg):
		self.outbox.append(msg)

	def recv(self, msg):
		return self.inbox.pop(msg)






def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()


def teardown(signum, frame):
	logging.info("shutdown start")

	# shutdown all running threads without passing references through global variables
	for thread in threading.enumerate():
		if hasattr(thread, "teardown") and callable(getattr(thread, "teardown")):
			thread.teardown()
			thread.join(1)

	logging.info("shutdown exit")


def main():
	"""main"""


	# args
	log_level = "info"
	args = parse_arguments()
	if args.debug:
		log_level = "debug"
	txaio.start_logging(level=log_level)

	# startup
	signal.signal(signal.SIGTERM, teardown)
	signal.signal(signal.SIGINT, teardown)
	thread_communicator = CommunicatorThread(args.server, args.realm, args.schema, log_level)
	thread_communicator.start()

	# there will be a loop

	thread_communicator.join()


if __name__ == "__main__":
	sys.exit(main())
