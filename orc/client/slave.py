#!/usr/bin/env python3
"""slave orc"""


import argparse
import communicator
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import txaio



class ExecThread(threading.Thread):
	"""subprocess in thread wrapper"""

	## object and thread management
	def __init__(self, comm, arguments, msg_type="message"):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = "exec"
		self.log = logging.getLogger()

		self.communicator = comm

		self.arguments = arguments
		self.msg_type = msg_type
		self.process = None
		self.shutdown = False


	def run(self):
		self.log.info("%s thread begin", self.name)

		self.process = subprocess.Popen(self.arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)

		while not self.shutdown:
			line = self.process.stdout.readline().rstrip().decode("utf-8")

			self.process.poll()
			if (not line) and (self.process.returncode is not None):
				break

			obj = {"Type": self.msg_type, "Message": line}
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



class SlaveShell():
	"""slave shell object"""

	## object and thread management
	def __init__(self):
		self.name = "slaveshell"
		self.log = logging.getLogger()

		self.communicator = None


	def run(self, args):
		"""main"""

		self.log.info("%s thread begin", self.name)

		self.communicator = communicator.CommunicatorThread(args.server, args.realm, args.schema, args.identity, self.handle_message)
		self.command_non([])

		self.communicator.start()
		self.communicator.join()

		self.log.info("%s thread end", self.name)

	def teardown(self):
		"""teardown component"""

		self.communicator.teardown()


	## appllication interface
	def handle_message(self, msg):
		"""handle incomming messages, communicator's callback"""

		self.log.debug("%s handle_message %s", self.name, msg)

		if msg["Type"] == "command":
			try:
				command_callable = "command_%s" % msg["Message"]["command"]
				if hasattr(self, command_callable) and callable(getattr(self, command_callable)):
					call = getattr(self, command_callable)
					call(msg["Message"]["arguments"])
			except Exception as e:
				self.log.error("%s invalid command %s %s", self.name, msg, e)


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

		data = [{"name": thread.name, "ident": thread.ident} for thread in threading.enumerate()]
		self.communicator.send_message({"Type": "tlist", "Message": data})


	def command_tstop(self, arguments): # pylint: disable=no-self-use
		"""stop threads"""

		for thread in threading.enumerate():
			if str(thread.ident) in arguments:
				thread.teardown()
				thread.join(10)


	def command_non(self, arguments):
		"""start netstat thread"""

		thread = ExecThread(self.communicator, ["python3", "-u", "../../tg/bin/netstat.py"] + arguments, "netstat")
		thread.name = "netstat"
		thread.start()

	def command_noff(self, arguments): # pylint: disable=no-self-use,unused-argument
		"""stop all netstat threads"""

		for thread in threading.enumerate():
			if thread.name == "netstat":
				thread.teardown()
				thread.join(10)



def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()

	parser.add_argument("--server", default="ws://127.0.0.1:56000/")
	parser.add_argument("--realm", default="orc1")
	parser.add_argument("--schema", default="orcish.schema")
	parser.add_argument("--identity", default=socket.getfqdn())
	parser.add_argument("--debug", action="store_true")

	return parser.parse_args()


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


def main():
	"""main"""

	# args
	args = parse_arguments()

	# txaio startup messes up standard logging
	logger = logging.getLogger()
	logger.handlers = []
	logger.setLevel(logging.INFO)
	txaio.start_logging(level="info")
	if args.debug:
		logger.setLevel(logging.DEBUG)
		txaio.start_logging(level="debug")

	# startup
	signal.signal(signal.SIGTERM, teardown)
	signal.signal(signal.SIGINT, teardown)
	SlaveShell().run(args)



if __name__ == "__main__":
	sys.exit(main())
