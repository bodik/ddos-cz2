"""runner module"""

import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import tg
import time



class Runner(object):
	"""executor holds code to execute the generator"""

	HEADER = """
#include "{tg_path}/bin/trafgen_stddef.h"
"""

	@staticmethod
	def build_arguments_parser(parser, generator):
		"""parse common arguments, add all layers parsers, generator specific arguments"""

		# generic arguments
		parser.add_argument("--debug", action="store_true", default=False, help="debug output")
		parser.add_argument("--dump", action="store_true", default=False, help="dump generator config")
		parser.add_argument("--dev", help="output iface; defaults to iface with default gw; eg. eth0")

		# timings
		parser.add_argument("--time", help="generate packets for specified time; eg. 2m3s")
		parser.add_argument("--num", help="number of packets to send")
		group_timing = parser.add_mutually_exclusive_group()
		group_timing.add_argument("--gap", help="interpacket gap")
		group_timing.add_argument("--rate", help="send rate")

		# generator specific
		for layer in [x for x in generator.LAYERS if isinstance(x, type)]:
			layer.parse_arguments(parser)
		generator.parse_arguments(parser)



	def __init__(self, generator, fields):
		"""initialize fields, run all layers postprocessors, generator specific postprocessing"""

		self.generator = generator
		self.fields = fields

		# generic fields
		self.fields["tg_path"] = os.path.dirname(os.path.realpath(sys.argv[0]))
		if not fields["dev"]:
			fields["dev"] = tg.utils.default_output_interface()

		# timings
		if self.fields["time"]:
			self.fields["time"] = tg.utils.parse_time(str(self.fields["time"]))

		# generator specifics
		for layer in [x for x in self.generator.LAYERS if isinstance(x, type)]:
			self.fields = layer.process_fields(self.fields)
		self.fields = self.generator.process_fields(self.fields)



	def compile(self):
		"""compile source for trafgen"""

		# compile source template for config from all layers
		template = self.HEADER
		for layer in self.generator.LAYERS:
			if isinstance(layer, type):
				template += layer.TEMPLATE
			else:
				template += layer

		# run template
		return template.format(**self.fields)



	def run(self):
		"""run trafgen"""

		# write config to filesystem
		ftmp = tempfile.NamedTemporaryFile(mode="w", prefix="tg2_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.compile())
		ftmp.close()

		# run trafgen
		trafgen_bin = "%s/bin/trafgen" % os.path.dirname(os.path.realpath(sys.argv[0]))
		cmd = [trafgen_bin, "--in", ftmp_name, "--out", self.fields["dev"], "--cpp"]
		for arg in [x for x in ["num", "gap", "rate"] if self.fields[x]]:
			cmd += ["--%s" % arg, str(self.fields[arg])]
		logging.debug(cmd)

		executor = tg.runner.TimedExecutor()
		signal.signal(signal.SIGTERM, executor.teardown)
		signal.signal(signal.SIGINT, executor.teardown)
		ret = executor.execute(cmd, self.fields["time"])

		# cleanup
		if ret == 0:
			logging.debug("cleaning up")
			os.unlink(ftmp_name)

		return ret



class TimedExecutor():
	"""timed executor, repeat execution/terminate process for/after specified time"""

	def __init__(self):
		self.log = logging.getLogger()
		self.process = None
		self.timer = None
		self.timer_finished = None # signal from timer
		self.timer_terminate = None # signal to timer


	def execute(self, cmd, seconds=None):
		if seconds:
			return self.execute_timed(cmd, seconds)
		else:
			return self.execute_once(cmd)


	def execute_once(self, cmd):
		"""execute once"""

		try:
			self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
			(process_stdout, process_stderr) = self.process.communicate()
			if process_stdout:
				self.log.debug(process_stdout.strip())
			if process_stderr:
				self.log.error(process_stderr.strip())
			if self.process.returncode != 0:
				self.log.error("exit code %s", self.process.returncode)
		except Exception as e:
			self.terminate_process()
			if self.process.returncode != 0:
				self.log.error("exit code %s", self.process.returncode)
			raise e

		return self.process.returncode


	def execute_timed(self, cmd, seconds):
		"""setup timer and execute until timer finishes"""

		if seconds < 1:
			raise ValueError("timer too low")
		self.process = None # ???
		self.timer = threading.Thread(name="TimedExecutorTimer", target=self.timer_thread, args=(seconds,))
		self.timer.setDaemon(True)
		self.timer_finished = False
		self.timer_terminate = False
		self.timer.start()

		while not self.timer_finished:
			self.execute_once(cmd)
			if self.process.returncode != 0:
				break

		self.timer_terminate = True
		self.timer.join()

		return self.process.returncode


	def terminate_process(self):
		"""terminate process"""

		self.process.poll()
		if self.process.returncode is None:
			os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
			self.process.wait()


	def timer_thread(self, seconds):
		"""actively wait for timeout and end running process"""

		self.log.debug("%s begin", threading.current_thread().name)
		while seconds > 0:
			time.sleep(1)
			seconds -= 1
			if self.timer_terminate:
				break
		self.timer_finished = True
		self.log.debug("%s end", threading.current_thread().name)

		self.terminate_process()


	def teardown(self, signum=None, frame=None):
		"""called by signal or external entitites to shutdown the executor"""

		self.log.info("aborted by signal")
		self.timer_terminate = True
		self.terminate_process()
