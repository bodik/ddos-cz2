#!/usr/bin/python
import argparse
import logging
import subprocess
import sys
import shlex
import time
import re
import datetime
import numpy

logger = logging.getLogger()

def parse_time(data):
	"""parse time spec 1h2m3s to total seconds"""

	regex = re.compile(r"^((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s?)?$")
	parts = regex.match(data)
	if not parts:
		raise ValueError("invalid time")
	parts = parts.groupdict()
	time_params = {}
	for (name, param) in parts.iteritems():
		if param:
			time_params[name] = int(param)

	return datetime.timedelta(**time_params).total_seconds()

class PerformanceTest(object):

	NGINX_CLEAR_LOG = "rm %s/access.log; kill -USR1 `cat %s/nginx.pid`"
	NGINX_GET_RESULTS = "cat %s/access.log | wc -l"
	NGINX_RUN_TEST = "pgrep nginx > /dev/null; echo $?"
	TSUNG_RUN = "/opt/ddos-cz2/tsung/pytsung %s --port %s --clients localhost -m %s --users %s --r 100000 --cpu %s --logdir /tmp/log --time %s"
	TSUNG_RUN_SSL = "/opt/ddos-cz2/tsung/pytsung %s --port %s --clients localhost -m %s --users %s --r 100000 --cpu %s --logdir /tmp/log --ssl --time %s"

	TESTBASE = [ \
		{"cpu" :  5, "method" : "GET", "ssl" : False, "users" :  "5000"},
		{"cpu" : 10, "method" : "GET", "ssl" : False, "users" : "10000"},
		{"cpu" : 20, "method" : "GET", "ssl" : False, "users" : "15000"},
		{"cpu" :  5, "method" : "GET", "ssl" : True,  "users" :  "5000"},
		{"cpu" : 10, "method" : "GET", "ssl" : True,  "users" : "10000"},
		{"cpu" : 20, "method" : "GET", "ssl" : True,  "users" : "15000"},
		{"cpu" :  5, "method" : "POST", "ssl" : False, "users" :  "5000"},
		{"cpu" : 10, "method" : "POST", "ssl" : False, "users" : "10000"},
		{"cpu" : 20, "method" : "POST", "ssl" : False, "users" : "15000"},
		{"cpu" :  5, "method" : "POST", "ssl" : True,  "users" :  "5000"},
		{"cpu" : 10, "method" : "POST", "ssl" : True,  "users" : "10000"},
		{"cpu" : 20, "method" : "POST", "ssl" : True,  "users" : "15000"}]

	def __init__(self, fields):
		self.process = None
		self.target = fields['target']
		self.port = fields['port']
		self.timeout = fields['timeout']
		self.remotelogs = fields['remotelogs']
		self.repetition = fields['repeat']
		self.delay = fields['delay']
		self.csv = fields['csv']

		if fields['list']:
			self.list_tests()
			sys.exit(0)

	def execute(self, cmd):
		return subprocess.check_output(shlex.split(cmd))

	def nginx_alive(self):
		res = self.execute("ssh %s \"%s\"" % (self.target, self.NGINX_RUN_TEST))
		if int(res) == 0:
			return True

		return False

	def nginx_clear_log(self):
		cmd = self.NGINX_CLEAR_LOG % (self.remotelogs, self.remotelogs)
		self.execute("ssh %s \"%s\"" % (self.target, cmd))
		return 0

	def nginx_get_results(self):
		cmd = self.NGINX_GET_RESULTS % (self.remotelogs)
		res = self.execute("ssh %s \"%s\"" % (self.target, cmd))
		return int(res)

	def tsung_run(self, params):
		cmd = ""
		if params['ssl']:
			cmd = self.TSUNG_RUN_SSL % (self.target, self.port, params['method'], params['users'], params['cpu'], self.timeout)
		else:
			cmd = self.TSUNG_RUN % (self.target, self.port, params['method'], params['users'], params['cpu'], self.timeout)
		subprocess.call(shlex.split(cmd))

	def list_tests(self):
		print "Available testing cases:"
		for i in xrange(0, len(self.TESTBASE)):
			if self.TESTBASE[i]['ssl']:
				print "  %2d. %9s, %2sx CPU, %5s users" % (i + 1, self.TESTBASE[i]['method'] + "(ssl)", self.TESTBASE[i]['cpu'], self.TESTBASE[i]['users'])
			else:
				print "  %2d. %9s, %2sx CPU, %5s users" % (i + 1, self.TESTBASE[i]['method'], self.TESTBASE[i]['cpu'], self.TESTBASE[i]['users'])

	def ssl_tests(self):
		return [test for test in self.TESTBASE if test['ssl']]

	def plain_tests(self):
		return [test for test in self.TESTBASE if not test['ssl']]

	def run(self, params):
		results = []

		method = params['method']
		if params['ssl']:
			method += "(ssl)"

		logger.info("Starting test (%s, %sxCPU, %s users)", method, params['cpu'], params['users'])

		for i in xrange(1, self.repetition + 1):
			logger.debug(" %d. Clear remote log", i)
			self.nginx_clear_log()
			logger.debug(" %d. Local Tsung started", i)
			self.tsung_run(params)
			logger.debug(" %d. Get remote results", i)
			results.append(self.nginx_get_results())

			if self.repetition > 1 and i < self.repetition + 1:
				time.sleep(self.delay)


		timeout_sec = parse_time(self.timeout)
		results_persec = [val / timeout_sec for val in results]

		median_sec = numpy.median(results_persec)
		min_sec = min(results_persec)
		max_sec = max(results_persec)
		mean_sec = numpy.mean(results_persec)
		std_sec = numpy.std(results_persec)

		if self.csv:
			print "%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f" % \
				(method, params['users'], params['cpu'], median_sec, min_sec, max_sec, mean_sec, std_sec)
		else:
			logger.info("RESULTS:")
			logger.info("Median %.2f, Min: %.2f, Max: %.2f, Mean: %.2f, Stddev: %.2f", median_sec, min_sec, max_sec, mean_sec, std_sec)

def main():
	"""main"""
	parser = argparse.ArgumentParser()
	parser.add_argument("target", help="destination ip or hostname")
	parser.add_argument("--port", type=int, default=44444, help="path to remote webserver log files")
	parser.add_argument("--timeout", "-t", default="2m", help="test timeout")
	parser.add_argument("--remotelogs", default="/usr/local/nginx/logs", help="path to remote webserver log files")
	parser.add_argument("--logfile", help="local logfile name")
	parser.add_argument("--repeat", "-r", type=int, default=1, help="number of repetition")
	parser.add_argument("--delay", "-d", type=int, default=20, help="Delay between each test")
	parser.add_argument("--csv", action="store_true", default=False, help="results in csv format")
	parser.add_argument("--test", help="'plain' / 'ssl' or commna separated tests; show numbers with --list directive")
	parser.add_argument("--list", action="store_true", default=False, help="list available testcases")
	parser.add_argument("--debug", action="store_true", default=False, help="set logging level to debug")

	args = vars(parser.parse_args())
	perftest = PerformanceTest(args)

	if args['logfile']:
		logging.basicConfig(level=logging.INFO, filename=args['logfile'], format='%(levelname)s %(message)s')
	else:
		logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')

	if args['debug']:
		logger.setLevel(logging.DEBUG)

	testcases = []
	if args['test']:
		if args['test'] == 'ssl':
			testcases = perftest.ssl_tests()
		elif args['test'] == 'plain':
			testcases = perftest.plain_tests()
		else:
			for i in args['test'].split(','):
				testcases.append(PerformanceTest.TESTBASE[int(i)-1])
	else:
		testcases = perftest.plain_tests()

	if perftest.nginx_alive():
		if args['csv']:
			logger.disabled = True
			print "### csv data"
			print "\"Method\",\"Users\",\"CPU [cores]\",\"Requests [req/s]\",\"Min [req/s]\"," \
								"\"Max [req/s]\",\"Mean [req/s]\",\"Std dev [req/s]\""
		for params in testcases:
			perftest.run(params)
	else:
		logger.info("Remote server or nginx down, exiting")
		sys.exit(1)


if __name__ == "__main__":
	sys.exit(main())
