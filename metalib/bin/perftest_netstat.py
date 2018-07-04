#!/usr/bin/python3
"""measure statistically processed netstat.py for command"""

import argparse
import csv
import datetime
import logging
import numpy
import os
import shlex
import signal
import socket
import subprocess
import sys
import time

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')



def sizeof_fmt(num, suffix="B"):
	"""convert to human readable form"""

	for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
		if abs(num) < 1000.0:
			return "%3.1f %1s%s" % (num, unit, suffix)
		num /= 1000.0
	return "%.1f %1s%s" % (num, "Y", suffix)



def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", action="store_true")

	#TODO: netstat detect default output iface by target ??
	parser.add_argument("--netstat_iface", default="eth0")

	# tg2
	parser.add_argument("--perftest_cmd", required=True)
	parser.add_argument("--perftest_time", type=int, default=10)
	return parser.parse_args()



def main():
	"""main"""

	## args and startup
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)
	logger.debug(args)
	basedir = os.path.dirname(os.path.realpath(__file__))
	proc_netstat_logfile = "/tmp/ddos-cz2_perftest.%d.log" % os.getpid()


	## start net monitor
	proc_netstat_log = open(proc_netstat_logfile, "w")
	cmd = "/usr/bin/python3 -u %s/netstat.py --iface %s --csv --noheader" % (basedir, args.netstat_iface)
	proc_netstat = subprocess.Popen(shlex.split(cmd), stdout=proc_netstat_log, stderr=proc_netstat_log)


	## perftested command
	proc_tested = subprocess.Popen(shlex.split(args.perftest_cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


	## run test
	try:
		time.sleep(args.perftest_time)
	except KeyboardInterrupt:
		logger.info("aborting")


	## shutdown test
	os.kill(proc_tested.pid, signal.SIGTERM)
	os.kill(proc_netstat.pid, signal.SIGTERM)
	proc_tested.wait()
	proc_netstat.wait()
	proc_netstat_log.close()


	## compute netstat statistics
	### read data
	data = []
	with open(proc_netstat_logfile, "r") as ftmp:
		for line in ftmp.read().splitlines():
			data.append([int(x) for x in line.split(",")])
	data = numpy.array(data)
	data_lines, data_columns = data.shape

	columns = [ \
		("rx_bits", "b"), ("rx_bytes", "B"), ("rx_packets", "p"),
		("tx_bits", "b"), ("tx_bytes", "B"), ("tx_packets", "p"),
		("tcp_open_active", " "), ("tcp_open_passive", " "),
		("tcp_listen", " "), ("tcp_established", " "),
		("tcp_close_active", " "), ("tcp_close_passive", " ")]
	fmt = "%-20s: mean= %10d, %10s ; median= %10d, %10s ; stddev= %10d, %10s"

	### compute statistics
	results = {}
	# colindex, colname, colunit
	for coli, (coln, colu) in enumerate(columns):
		values = data[:, coli]
		mean, median, stddev = numpy.mean(values), numpy.median(values), numpy.std(values)
		results[coln] = ((mean, sizeof_fmt(mean, colu)), (median, sizeof_fmt(median, colu)), (stddev, sizeof_fmt(stddev, colu)))


	### print results
	print("## Perftest netstat results")
	print("%-20s: %s" % ("node", socket.getfqdn()))
	print("%-20s: %s" % ("date", datetime.datetime.now().isoformat()))
	print("%-20s: %s" % ("perftested cmd", args.perftest_cmd))
	print("%-20s: %s" % ("datapoints", data_lines))
	for coli, (coln, colu) in enumerate(columns):
		# cast all tuples to list, sum the list to empty one to get flat list of values, cast to tuple for fmt
		fmt_data = tuple(sum(map(list, results[coln]), [coln]))
		print(fmt % fmt_data)

	header = ["node", "date", "perftested cmd", "datapoints"]
	values_fmt = ["%s", "%s", "%s", "%d"]
	values = [socket.getfqdn(), datetime.datetime.now().isoformat(), args.perftest_cmd, data_lines]
	for coli, (coln, colu) in enumerate(columns):
		for value in ["mean", "median", "stddev"]:
			header.append("%s-%s" % (coln, value))
			header.append("%s-%s-human" % (coln, value))
			values_fmt.append("%d")
			values_fmt.append("%s")
		values += sum(map(list, results[coln]), [])

	print("### csv data")
	csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_NONNUMERIC)
	csvwriter.writerow(header)
	csvwriter.writerow(values)



if __name__ == "__main__":
	main()
