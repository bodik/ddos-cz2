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
	"""wamp transport communication component"""

	## object and thread management
	def __init__(self, url, realm, message_schema, identity, message_handler=None):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "communicator"
		self.log = logging.getLogger()

		# autobahn
		self.loop = None
		self.session = None
		self.component = autobahn.asyncio.component.Component(transports=[{"url": url}], realm=realm)
		self.component.on("connect", self.session_on_connect)
		self.component.on("join", self.session_on_join)
		self.component.on("ready", self.session_on_ready)
		self.component.on("leave", self.session_on_leave)
		self.component.on("disconnect", self.session_on_disconnect)

		# communicator
		self.identity = identity
		with open(message_schema, "r") as ftmp:
			self.message_schema = json.loads(ftmp.read())
		self.message_handler = message_handler
		self.topic = "ddos-cz2.common"


	def run(self):
		self.log.debug("%s thread begin", self.name)

		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)
		txaio.config.loop = self.loop

		self.component.start(loop=self.loop)
		try:
			self.loop.run_forever()
		except asyncio.CancelledError:
			pass

		self.loop.stop()
		self.loop.close()

		self.log.debug("%s thread end", self.name)


	def teardown_real(self):
		"""should end the communicator from within communicator's thread"""

		self.log.debug("%s teardown_real begin", self.name)

		@asyncio.coroutine
		def exitcoro():
			"""exit coroutine"""
			return self.loop.stop()

		try:
			self.component.stop()
		except Exception as e:
			self.log.error(e)

		for task in asyncio.Task.all_tasks():
			self.log.info("canceling: %s", task)
			task.cancel()
		asyncio.ensure_future(exitcoro())

		self.log.debug("%s teardown_real end", self.name)


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.log.debug("%s teardown begin", self.name)
		self.loop.call_soon_threadsafe(self.teardown_real)
		self.log.debug("%s teardown end", self.name)


	## application interface
	def session_on_connect(self, session, protocol):
		"""on connect"""

		self.log.debug("%s connected %s %s", self.name, session, protocol)


	def session_on_join(self, session, details):
		"""on join"""

		self.log.debug("%s joined %s %s", self.name, session, details)
		self.session = session

		self.session.subscribe(self.receive_message, self.topic, options=autobahn.wamp.types.SubscribeOptions(details=True))


	def session_on_ready(self, session):
		"""on ready"""

		self.log.debug("%s ready %s", self.name, session)


	def session_on_leave(self, session, details):
		"""on leave"""

		self.log.debug("%s left %s %s", self.name, session, details)
		self.session = None


	def session_on_disconnect(self, session, was_clean):
		"""on disconnect"""

		self.log.debug("%s disconnected %s %s", self.name, session, was_clean)


	def receive_message(self, message, details=None):
		"""receive message, transport callback"""

		try:
			jsonschema.validate(message, self.message_schema)
		except jsonschema.exceptions.ValidationError:
			self.log.warning("%s invalid message %s %s", self.name, message, details)
			return

		self.log.debug("%s message %s %s", self.name, message, details)
		if callable(self.message_handler):
			self.message_handler(message)


	def send_message(self, obj):
		"""send message, transport service"""

		try:
			if self.session:
				obj["Id"] = str(uuid.uuid4())
				obj["Node"] = self.identity
				self.session.publish(self.topic, obj)
		except Exception as e:
			self.log.warning(e)
			return False

		return obj
