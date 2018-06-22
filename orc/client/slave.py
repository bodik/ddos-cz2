#!/usr/bin/env python3

import argparse
import asyncio
import autobahn.asyncio.wamp
import autobahn.wamp.types
import json
import jsonschema
import logging
import os
import time
import txaio
import signal
import sys

txaio.use_asyncio()


class Slave(autobahn.asyncio.wamp.ApplicationSession):
	"""slave orc"""

	def __init__(self, *args, **kwargs):
		super(Slave, self).__init__(*args, **kwargs)
	
		self.received = 0	
		self.msg_schema = {}
		if "msg_schema" in self.config.extra:
			self.msg_schema = self.config.extra["msg_schema"]


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
			valid = True
		except jsonschema.exceptions.ValidationError:
			valid = False
		self.log.info("{cls}: {valid} message {msg}", cls=self.__class__.__name__, valid=valid, msg=msg)

		self.received += 1
		if self.received > 30:
			self.leave()



def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()
	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")

	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()


def main():
	# args
	"""main"""
	log_level = "info"
	args = parse_arguments()
	if args.debug:
		log_level = "debug"

	# startup
	txaio.start_logging(level=log_level)
	
	with open(args.schema, "r") as ftmp:
		msg_schema = json.loads(ftmp.read())

	shutdown = False
	while not shutdown:
		try:
			## code mainly taken from ApplicationRunner but can handle repeating router failures/disconnects
			loop = asyncio.get_event_loop()
			if loop.is_closed():
				asyncio.set_event_loop(asyncio.new_event_loop())
				loop = asyncio.get_event_loop()

			runner = autobahn.asyncio.wamp.ApplicationRunner(args.server, realm=args.realm, extra={"msg_schema": msg_schema})
			coro = runner.run(Slave, start_loop=False, log_level=log_level)
			(transport, protocol) = loop.run_until_complete(coro)
			loop.add_signal_handler(signal.SIGTERM, loop.stop)
			try:
				loop.run_forever()
			except KeyboardInterrupt:
				logging.info("aborted by user")
				shutdown = True
			if protocol._session:
				loop.run_until_complete(protocol._session.leave())
			loop.close()

		except Exception as e:
			logging.error(e)
			try:
				time.sleep(1)
			except KeyboardInterrupt:
				shutdown = True


if __name__ == "__main__":
	sys.exit(main())
