#!/usr/bin/env python3

import asyncio
import autobahn.asyncio.wamp
import json
import logging
import os
import time
import txaio
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
			runner = autobahn.asyncio.wamp.ApplicationRunner(url, realm)
			runner.run(Slave, log_level="debug")
		except Exception as e:
			logging.error(e)
			time.sleep(1)
		except KeyboardInterrupt:
			logging.info("aborted by user")
			shutdown = True


if __name__ == "__main__":
	sys.exit(main())
