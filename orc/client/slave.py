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


class CommunicatorWampSession(autobahn.asyncio.wamp.ApplicationSession):

	def __init__(self, *args, **kwargs):
		super(CommunicatorWampSession, self).__init__(*args, **kwargs)
		self.received = 0
		self.msg_schema = self.config.extra["msg_schema"]
		self.communicator_thread = self.config.extra["communicator_thread"]

	async def onJoin(self, details):
		def on_message(msg, details):
			self.receiveMessage(msg)

		self.log.info("{cls}: joined {details}", cls=self.__class__.__name__, details=details)
		await self.subscribe(on_message, "ddos-cz2.slaves", options=autobahn.wamp.types.SubscribeOptions(details=True))

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

	def receiveMessage(self, msg):
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

	def __init__(self, url, realm, msg_schema):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "communicator"
		self.log = logging.getLogger()

		# communicator
		with open(msg_schema, "r") as ftmp:
			self.msg_schema = json.loads(ftmp.read())
		self.shutdown = False

		# asyncio
		self.loop = None

		# autobahn config and session
		self.session = None
		self.url = url
		self.realm = realm
		self.ssl = None
		self.extra = {"communicator_thread": self, "msg_schema": self.msg_schema}


	def run(self):
		self.log.info("start %s", self.name)

		# setup loop for current thread
		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)

		# loop runner/reconnect until shutting down
		while not self.shutdown:
			try:
				self.applicationRunner()
			except Exception as e:
				self.log.error(e)
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					self.log.info("aborted by user")
					self.shutdown = True

		self.log.info("end %s", self.name)

	def applicationRunner(self):
		"""application runner taken from autobahn.asyncio.wamp to have own session object"""
		# runner is reimplemented for 2 main reasons:
		# 	a) having callable session within thread/object, it might be injected into runner (make attr), but
		# 	b) handling KeyboardInterrupt requires external loop anyway

		# session
		cfg = autobahn.wamp.types.ComponentConfig(self.realm, self.extra)
		self.session = CommunicatorWampSession(cfg)

		# transport factory
		isSecure, host, port, resource, path, params = autobahn.websocket.util.parse_url(self.url)
		transport_factory = autobahn.asyncio.websocket.WampWebSocketClientFactory(self.session, url=self.url, serializers=None, proxy=None, headers=None)

		# connection options
		offers = [autobahn.websocket.compress.PerMessageDeflateOffer()]
		def accept(response):
			if isinstance(response, autobahn.websocket.compress.PerMessageDeflateResponse):
				return autobahn.websocket.compress.PerMessageDeflateResponseAccept(response)
		transport_factory.setProtocolOptions( \
			maxFramePayloadSize=1048576,
			maxMessagePayloadSize=1048576,
			autoFragmentSize=65536,
			failByDrop=False,
			openHandshakeTimeout=2.5,
			closeHandshakeTimeout=1.0,
			tcpNoDelay=True,
			autoPingInterval=10.0,
			autoPingTimeout=5.0,
			autoPingSize=4,
			perMessageCompressionOffers=offers,
			perMessageCompressionAccept=accept)

		#runner ssl stuff missing
		if self.ssl is None:
			ssl = isSecure
		else:
			if self.ssl and not isSecure:
				raise RuntimeError('ssl argument value passed to %s conflicts with the "ws:" prefix of the url argument.')
			ssl = self.ssl

		# start the client connection
		self.loop = asyncio.get_event_loop()
		if self.loop.is_closed():
			asyncio.set_event_loop(asyncio.new_event_loop())
			self.loop = asyncio.get_event_loop()
			if hasattr(transport_factory, "loop"):
				transport_factory.loop = self.loop

		txaio.use_asyncio()
		txaio.config.loop = self.loop
		coro = self.loop.create_connection(transport_factory, host, port, ssl=ssl)

		# start asyncio loop
		(transport, protocol) = self.loop.run_until_complete(coro)
		try:
		        self.loop.run_forever()
		except KeyboardInterrupt:
		        self.log.info("aborted by user")
		        self.shutdown = True

		if protocol._session:
		        self.loop.run_until_complete(protocol._session.leave())
		
		self.loop.close()
		self.session = None


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.log.info("shutting down %s", self.name)
		self.shutdown = True
		self.loop.stop()



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
	logger.info("shutdown start")

	# shutdown all running threads without passing references through global variables
	for thread in threading.enumerate():
		if hasattr(thread, "teardown") and callable(getattr(thread, "teardown")):
			thread.teardown()
			thread.join(1)

	logger.info("shutdown exit")


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
