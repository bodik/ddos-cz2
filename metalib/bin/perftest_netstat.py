#!/usr/bin/python3

import argparse
import logging
import numpy
import os
import shlex
import signal
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
	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", action="store_true")

	#TODO: netstat detect default output iface by target ??
	parser.add_argument("--netstat_iface", default="eth0")

	# tg2
	parser.add_argument("--perftest_cmd", required=True)
	parser.add_argument("--perftest_time", type=int, default=10)
	return parser.parse_args()



def main():
	# args and startup
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)
	logger.debug(args)
	basedir = os.path.dirname(os.path.realpath(__file__))
	proc_netstat_logfile = "/tmp/ddos-cz2_perftest.%d.log" % os.getpid()


	# start net monitor
	proc_netstat_log = open(proc_netstat_logfile, "w")
	cmd = "/usr/bin/python3 -u %s/netstat.py --iface %s --csv --noheader" % (basedir, args.netstat_iface)
	proc_netstat = subprocess.Popen(shlex.split(cmd), stdout=proc_netstat_log, stderr=proc_netstat_log)


	# perftested command
	#./tg2 UdpRandomPayload --ip4_source_address drnd --ip4_destination_address 78.128.217.226 --length 0
	proc_tested = subprocess.Popen(shlex.split(args.perftest_cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


	# run test
	try:
		time.sleep(args.perftest_time)
	except KeyboardInterrupt:
		logger.info("aborting")


	# shutdown test
	os.kill(proc_tested.pid, signal.SIGTERM)
	os.kill(proc_netstat.pid, signal.SIGTERM)
	proc_tested.wait()
	proc_netstat.wait()
	proc_netstat_log.close()


	# compute netstat statistics
	## read data
	data = []
	with open(proc_netstat_logfile, "r") as ftmp:
		for line in ftmp.read().splitlines():
			data.append([int(x) for x in line.split(",")])
	data = numpy.array(data)


	## compute stats
	columns = [ \
		"rx_bits", "rx_bytes", "rx_packets",
		"tx_bits", "tx_bytes", "tx_packets",
		"tcp_open_active", "tcp_open_passive",
		"tcp_listen", "tcp_established",
		"tcp_close_active", "tcp_close_passive"]
	columns_humanized = [ \
		"b", "B", "p",
		"b", "B", "p",
		" ", " ", " ",
		" ", " ",
		" ", " ", " "]
	fmt = "%-20s: mean= %10d, %10s ; median= %10d, %10s ; stddev= %10d, %10s"

	for col in range(len(columns)):
		values = data[:,col]
		mean, median, stddev = numpy.mean(values), numpy.median(values), numpy.std(values)
		print(fmt % ( \
			columns[col],
			mean, sizeof_fmt(mean, columns_humanized[col]),
			median, sizeof_fmt(median, columns_humanized[col]),
			stddev, sizeof_fmt(stddev, columns_humanized[col])))



if __name__ == "__main__":
	main()
