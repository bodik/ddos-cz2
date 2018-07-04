#!/usr/bin/python
import argparse
import logging
import subprocess
import sys
import shlex
import time

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')

def median(values):
	values = sorted(values)
	values_len = len(values)
	if values_len < 1:
		return None
	if values_len % 2 == 0:
		return (values[(values_len-1)/2] + values[(values_len+1)/2]) / 2.0
	else:
		return values[(values_len-1)/2]

class PerformanceTest(object):

	TEST_DELAY = 10
	NGINX_CLEAR_LOG = "rm %s/access.log; kill -USR1 `cat %s/nginx.pid`"
	NGINX_GET_RESULTS = "cat %s/access.log | wc -l"
	NGINX_RUN_TEST = "pgrep nginx > /dev/null; echo $?"
	TSUNG_RUN = "/opt/ddos-cz2/tsung/pytsung %s --port %s --clients localhost -m %s --users %s --r 100000 --cpu %s --logdir log --time 1m"
	TSUNG_RUN_SSL = "/opt/ddos-cz2/tsung/pytsung %s --port %s --clients localhost -m %s --users %s --r 100000 --cpu %s --logdir log --ssl --time 1m"

	TESTBASE = [ \
		{"cpu" :  5, "method" :  "GET", "ssl" : False, "users" :  "5000"},
		{"cpu" : 10, "method" :  "GET", "ssl" : False, "users" : "10000"},
		{"cpu" : 20, "method" :  "GET", "ssl" : False, "users" : "15000"},
		{"cpu" :  5, "method" :  "GET", "ssl" : True,  "users" :  "5000"},
		{"cpu" : 10, "method" :  "GET", "ssl" : True,  "users" : "10000"},
		{"cpu" : 20, "method" :  "GET", "ssl" : True,  "users" : "15000"},
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
		self.remotelogs = fields['remotelogs']
		self.repetition = fields['repeat']

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
			cmd = self.TSUNG_RUN_SSL % (self.target, self.port, params['method'], params['users'], params['cpu'])
		else:
			cmd = self.TSUNG_RUN % (self.target, self.port, params['method'], params['users'], params['cpu'])
		subprocess.call(shlex.split(cmd))

	def list_tests(self):
		print "Available testing cases:"
		for i in xrange(0, len(self.TESTBASE)):
			print "  %2d. %4s, %2sx CPU, %5s users" % (i + 1, self.TESTBASE[i]['method'], self.TESTBASE[i]['cpu'], self.TESTBASE[i]['users'])

	def run(self, params):
		results = []

		if params['ssl']:
			logger.info("Starting test (%s(ssl), %sxCPU, %s users)", params['method'], params['cpu'], params['users'])
		else:
			logger.info("Starting test (%s, %sxCPU, %s users)", params['method'], params['cpu'], params['users'])

		for i in xrange(1, self.repetition + 1):
			logger.debug(" %d. Clear remote log", i)
			self.nginx_clear_log()
			logger.debug(" %d. Local Tsung started", i)
			self.tsung_run(params)
			logger.debug(" %d. Get remote results", i)
			results.append(self.nginx_get_results())

			if self.repetition > 1:
				time.sleep(self.TEST_DELAY)

		logger.info("RESULTS:")
		logger.info("Values: %s", results)
		logger.info("Median: %s, Min: %s, Max: %s", median(results), min(results), max(results))
		logger.info("")

def main():
	"""main"""
	parser = argparse.ArgumentParser()
	parser.add_argument("target", help="destination ip or hostname")
	parser.add_argument("--port", type=int, default=44444, help="path to remote webserver log files")
	parser.add_argument("--remotelogs", default="/usr/local/nginx/logs", help="path to remote webserver log files")
	parser.add_argument("--repeat", "-r", type=int, default=1, help="number of repetition")
	parser.add_argument("--logfile", "-l", default="results.log", help="file with results")
	parser.add_argument("--test", help="commna separated tests; show numbers with --list directive")
	parser.add_argument("--list", action="store_true", default=False, help="list available testcases")
	parser.add_argument("--debug", action="store_true", default=False, help="set logging level to debug")

	args = vars(parser.parse_args())
	perftest = PerformanceTest(args)

	if args['debug']:
		logger.setLevel(logging.DEBUG)

	testcases = []
	if args['test']:
		for i in args['test'].split(','):
			testcases.append(PerformanceTest.TESTBASE[int(i)-1])
	else:
		testcases = PerformanceTest.TESTBASE

	if perftest.nginx_alive():
		for params in testcases:
			perftest.run(params)
			time.sleep(PerformanceTest.TEST_DELAY)
	else:
		logger.info("Remote server or nginx down, exiting")
		sys.exit(1)


if __name__ == "__main__":
	sys.exit(main())
