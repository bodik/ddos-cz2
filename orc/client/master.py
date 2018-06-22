#!/usr/bin/env python3

import asyncio
import autobahn.asyncio.wamp
import autobahn.wamp.types
import logging
import random
import os
import sys
import uuid

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s %(message)s')


class Master(autobahn.asyncio.wamp.ApplicationSession):
	"""master orc"""

	async def onJoin(self, details):
		counter = 0
		while True:
			obj = {"counter": counter, "foo": [1, 2, 3]}
			logger.debug("publish: ddos-cz2.slaves")
			self.publish(u"ddos-cz2.slaves", msg=obj)
			counter += 1

			obj = {"Id": str(uuid.uuid4()), "Type": "test"}
			logger.debug("publish: ddos-cz2.slaves")
			self.publish(u"ddos-cz2.slaves", msg=obj)
			counter += 1

			await asyncio.sleep(1)


if __name__ == "__main__":
	url = os.environ.get("ORC_ROUTER", u"ws://127.0.0.1:56000/ws")
	realm = u"orc1"
	runner = autobahn.asyncio.wamp.ApplicationRunner(url, realm)
	runner.run(Master, log_level='debug')
