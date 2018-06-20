#!/usr/bin/python
"""runner module"""

import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import tsung
import time
import string
import cgi

class TsungTemplate(string.Template):
        delimiter = '__TSUNG_'

class Runner(object):
	"""executor holds code to execute the generator"""

        CLIENT_CONFIG = "\t<client host=\"%s\" maxusers=\"10000\" use_controller_vm=\"true\"><ip scan=\"true\" value=\"%s\"/></client>\n"
        TSUNG_BIN = "/opt/tsung/bin/tsung"

	def __init__(self, fields):
		"""initialize fields, run all layers postprocessors, generator specific postprocessing"""
		
                self.fields = fields

		# generic fields
		self.fields['tsung_path'] = os.path.dirname(os.path.realpath(sys.argv[0]))
		if not fields['dev']:
		    fields['dev'] = tsung.utils.default_output_interface()

		# timings
		if self.fields['time']:
		    self.fields['time'] = tsung.utils.parse_time(str(self.fields['time']))

                # content and method check
                if self.fields['content'] and self.fields['method'] == 'GET':
                    print "ERROR: HTTP GET method not supports content in request, remove --data option."
                    sys.exit(1)

                # custom template
                if not self.fields['template']:
                    self.fields['template'] = "%s/templates/template.xml" % (self.fields['tsung_path'])

	def compile(self):
		"""replace template for tsung"""
                #read template from file, fill with args

                secure = "ssl" if self.fields['ssl'] else "tcp"
                
                clients = ""
                for cl in self.fields['clients'].split(','):
                    clients += self.CLIENT_CONFIG % (cl, self.fields['dev'])

                content = ""
                if self.fields['content'].startswith('file://'):
                    with open(self.fields['content'][7:], 'r') as contentfile:
                        content = cgi.escape(contentfile.read())
                else:
                    content = cgi.escape(self.fields['content'])

                res = ""
                with open(self.fields['template'], 'r') as template:
                      data = template.read()
                      t = TsungTemplate(data)
                      d = { 'host'    : self.fields['host'],
                            'port'    : self.fields['port'],
                            'clients' : clients,
                            'secure'  : secure,
                            'users'   : self.fields['users'],
                            'requests': self.fields['requests'],
                            'uri'     : self.fields['uri'],
                            'method'  : self.fields['method'],
                            'content' : content
                          }

                      res = t.safe_substitute(d)

		return res


	def run(self):
		"""run tsung"""
		# write config to filesystem
		ftmp = tempfile.NamedTemporaryFile(prefix="tsung_generator_", delete=False)
		ftmp_name = ftmp.name
		ftmp.write(self.compile())
		ftmp.close()

                logging.debug(ftmp_name)

		# run tsung
		#tsung_bin = "%s/bin/tsung" % os.path.dirname(os.path.realpath(sys.argv[0]))
                if self.fields['logdir']:
                    cmd = [self.TSUNG_BIN, "-f", ftmp_name, "-l", self.fields['logdir'], "start"]
                else:
                    cmd = [self.TSUNG_BIN, "-f", ftmp_name, "start"]

		logging.debug(cmd)
		try:
			if self.fields["time"]:
				ret = tsung.runner.TimedExecutor().execute(cmd, self.fields["time"])
			else:
				ret = tsung.runner.TimedExecutor().execute_once(cmd)
		except KeyboardInterrupt:
			logging.info("aborted by user")
			ret = 0

		# cleanup
		if ret == 0:
			logging.debug("cleaning up")
			os.unlink(ftmp_name)

		return ret



class TimedExecutor(object):
	"""timed executor, repeat execution/terminate process for/after specified time"""

	def __init__(self):
		self.process = None
		self.timer = None
		self.timer_finished = None # signal from timer
		self.timer_terminate = None # signal to timer


	def execute_once(self, cmd):
		try:
			self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
			(process_stdout, process_stderr) = self.process.communicate()
			if process_stdout:
				logging.debug(process_stdout.strip())
			if process_stderr:
				logging.error(process_stderr.strip())
			if self.process.returncode != 0 and self.process.returncode != -15:
				logging.error("exit code %s", self.process.returncode)
		except (Exception, KeyboardInterrupt) as e:
			self.terminate_process()
			if self.process.returncode != 0 and self.process.returncode != -15:
				logging.error("exit code %s", self.process.returncode)
			raise e

		return self.process.returncode


	def execute(self, cmd, seconds):
		"""setup timer and execute until timer finishes"""

		if seconds < 1:
			raise ValueError("timer too low")
		self.process = None
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
		self.process.poll()
		if self.process.returncode is None:
			os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
			self.process.wait()


	def timer_thread(self, seconds):
		"""actively wait for timeout and end running process"""

		logging.debug("%s begin", self.__class__.__name__)
		while seconds > 0:
			time.sleep(1)
			seconds -= 1
			if self.timer_terminate:
				break
		self.timer_finished = True
		logging.debug("%s end", self.__class__.__name__)

		self.terminate_process()
