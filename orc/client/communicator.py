#!/usr/bin/env python3
"""communicator threaded module"""


import asyncio
import autobahn.asyncio.component
import autobahn.wamp.types
import json
import jsonschema
import logging
import threading
import txaio
import uuid



class CommunicatorThread(threading.Thread):

	## object and thread management
	def __init__(self, url, realm, msg_schema, msg_callback=None):
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
		self.topic = "ddos-cz2.common"
		self.msg_callback = msg_callback


	def run(self):
		self.log.info("thread %s begin", self.name)

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

		self.log.info("thread %s end", self.name)


	def teardown_real(self):
		"""should end the communicator from within communicator's thread"""

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

		self.session.subscribe(self.receiveMessage, self.topic, options=autobahn.wamp.types.SubscribeOptions(details=True))


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

		self.log.debug("%s: message %s %s", self.name, msg, details)
		if callable(self.msg_callback):
			self.msg_callback(msg)


	def sendMessage(self, obj):
		try:
			if self.session:
				self.session.publish(self.topic, obj)
		except Exception as e:
			self.log.warn(e)
			return False

		return True
