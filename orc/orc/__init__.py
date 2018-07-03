"""orc module"""


import logging
import orc.communicator
import orc.ui
import os
import shlex
import signal
import subprocess
import threading
import time
import txaio


def start_logging(debug=False):
	"""startup logging, autobahn using txiao is little messy"""

	logger = logging.getLogger()
	logger.handlers = []
	logger.setLevel(logging.INFO)
	txaio.start_logging(level="info")
	if debug:
		logger.setLevel(logging.DEBUG)
		txaio.start_logging(level="debug")


def teardown(signum, frame): # pylint: disable=unused-argument
	"""signal handler, try to shutdown all threads"""

	logger = logging.getLogger()
	logger.info("signaled teardown begin")

	# shutdown all running threads without passing references through global variables
	for thread in threading.enumerate():
		if hasattr(thread, "teardown") and callable(getattr(thread, "teardown")):
			thread.teardown()
			thread.join(10)

	logger.info("signaled teardown end")



class ExecThread(threading.Thread):
	"""subprocess in thread wrapper"""

	## object and thread management
	def __init__(self, comm, arguments, message_type="message"):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "exec"
		self.log = logging.getLogger()

		self.communicator = comm

		self.arguments = arguments
		self.message_type = message_type
		self.process = None
		self.shutdown = False


	def run(self):
		self.log.info("%s thread begin", self.name)

		try:
			self.process = subprocess.Popen(self.arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)

			while not self.shutdown:
				line = self.process.stdout.readline().rstrip().decode("utf-8")
				self.process.poll()
				if (not line) and (self.process.returncode is not None):
					break
				obj = {"Type": self.message_type, "Message": line}
				self.communicator.send_message(obj)
		except Exception as e:
			self.log.error(e)
			obj = {"Type": self.message_type, "Message": str(e)}
			self.communicator.send_message(obj)


		self.log.info("%s thread end", self.name)


	def teardown(self):
		"""called from external objects to singal gracefull teardown request"""

		self.shutdown = True
		self.terminate_process()


	def terminate_process(self):
		"""terminate process"""

		self.process.poll()
		if self.process.returncode is None:
			os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
			self.process.wait()



class Slave(object):
	"""slave object"""

	## object and thread management
	def __init__(self):
		self.name = "slave"
		self.log = logging.getLogger()

		self.communicator = None


	def run(self, args):
		"""main"""

		self.log.info("%s thread begin", self.name)

		self.communicator = orc.communicator.CommunicatorThread(args.server, args.realm, args.schema, args.identity, self.handle_message)
		self.command_non([]) #TODO: only for dev purposes, will be removed for release
		self.communicator.start()
		self.communicator.join()

		self.log.info("%s thread end", self.name)

	def teardown(self):
		"""teardown component"""

		self.communicator.teardown()


	## appllication interface
	def handle_message(self, message):
		"""handle incomming messages, communicator's callback"""

		self.log.debug("%s handle_message %s", self.name, message)

		if message["Type"] == "command":
			try:
				command_callable = "command_%s" % message["Message"]["command"]
				if hasattr(self, command_callable) and callable(getattr(self, command_callable)):
					call = getattr(self, command_callable)
					call(message["Message"]["arguments"])
			except Exception as e:
				self.log.error("%s invalid command %s %s", self.name, message, e)


	def command_nodes(self, arguments): # pylint: disable=unused-argument
		"""reply to application ping"""

		data = subprocess.check_output(["uname", "-a"]).rstrip().decode("utf-8")
		self.communicator.send_message({"Type": "nodes", "Message": data})


	def command_exec(self, arguments):
		"""execute in thread"""

		thread = ExecThread(self.communicator, arguments)
		thread.start()

	def command_tlist(self, arguments): # pylint: disable=unused-argument
		"""list current process threads"""

		data = [{"name": thread.name, "ident": thread.ident, "arguments": getattr(thread, "arguments", None)} for thread in threading.enumerate()]
		self.communicator.send_message({"Type": "tlist", "Message": data})

	def command_tstop(self, arguments): # pylint: disable=no-self-use
		"""stop threads"""

		for thread in threading.enumerate():
			if str(thread.ident) in arguments:
				thread.teardown()
				thread.join(10)


	def command_non(self, arguments):
		"""start netstat thread"""

		thread = ExecThread(self.communicator, ["/usr/bin/python3", "-u", "../metalib/bin/netstat.py"] + arguments, "netstat")
		thread.name = "netstat"
		thread.start()

	def command_noff(self, arguments): # pylint: disable=no-self-use,unused-argument
		"""stop all netstat threads"""

		for thread in threading.enumerate():
			if thread.name == "netstat":
				thread.teardown()
				thread.join(10)


	def command_tg(self, arguments):
		"""start trafgen shortcut"""

		thread = ExecThread(self.communicator, ["/usr/bin/python3", "-u", "../tg/tg2"] + arguments, "tg2")
		thread.name = "tg2"
		thread.start()

	def command_tgoff(self, arguments): # pylint: disable=no-self-use,unused-argument
		"""stop all trafgen"""

		for thread in threading.enumerate():
			if thread.name == "tg2":
				os.killpg(os.getpgid(thread.process.pid), signal.SIGTERM)






class Master(object):
	"""master object"""

	## object and thread management
	def __init__(self):
		self.name = "master"
		self.log = logging.getLogger()

		self.communicator = None
		self.console = None
		self.shutdown = False


	def run(self, args):
		"""main"""

		self.log.debug("%s thread begin", self.name)
		self.communicator = orc.communicator.CommunicatorThread(args.server, args.realm, args.schema, args.identity, self.handle_message)
		self.communicator.start()

		if args.ui == "formed":
			self.console = orc.ui.Formed("[%s] %s %s" % (args.identity, args.server, args.realm), self.handle_command)

		if args.ui == "listener":
			self.console = orc.ui.Listener()

		if args.ui == "commander":
			self.console = orc.ui.Commander(self.handle_command)
			timeout = 10
			while (not self.communicator.session) and (timeout > 0):
				self.log.info("waiting on session")
				timeout -= 1
				time.sleep(1)

		try:
			self.console.run()
		except KeyboardInterrupt:
			pass

		self.communicator.teardown()
		self.communicator.join()
		self.log.debug("%s thread end", self.name)


	def teardown(self):
		"""teardown component"""
		pass


	## application interface
	def handle_message(self, message):
		"""handle incomming messages, communicator's callback"""

		self.console.handle_message(message)


	def handle_command(self, command):
		"""reply to application ping"""

		if command:
			cmd = shlex.split(command)
			obj = {"Type": "command", "Message": {"command": cmd[0], "arguments": cmd[1:]}}
			obj = self.communicator.send_message(obj)
			self.console.handle_message(obj)
