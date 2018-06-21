#!/usr/bin/env python3

import asyncio
import autobahn.asyncio.wamp
import json
import logging
import os
import time
import txaio
import signal
import sys

txaio.use_asyncio()


class Slave(autobahn.asyncio.wamp.ApplicationSession):
	"""slave orc"""
	received = 0

	async def onJoin(self, details):

		def on_message(msg):
			self.log.debug("{cls}: got event {msg}", cls=self.__class__.__name__, msg=msg)
			self.received += 1
			if self.received > 5:
				self.leave()

		await self.subscribe(on_message, u"ddos-cz2.slaves")

	def onDisconnect(self):
		asyncio.get_event_loop().stop()


def main():
	# args
	url = os.environ.get("ORC_ROUTER", u"ws://127.0.0.1:56000/ws")
	realm = u"orc1"
	txaio.start_logging(level="debug")

	shutdown = False
	while not shutdown:
		try:
			## code mainly taken from ApplicationRunner but can handle repeating router failures/disconnects
			loop = asyncio.get_event_loop()
			if loop.is_closed():
				asyncio.set_event_loop(asyncio.new_event_loop())
				loop = asyncio.get_event_loop()

			runner = autobahn.asyncio.wamp.ApplicationRunner(url, realm)
			coro = runner.run(Slave, start_loop=False, log_level="debug")
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
