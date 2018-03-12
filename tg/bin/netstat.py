#!/usr/bin/python

import argparse
import logging
import time
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')
logger = logging.getLogger()


def parse_arguments():
	"""parse arguments"""

	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--time", type=int, default=1, help="time period")
	parser.add_argument("--single", action="store_true", help="print one statistic and exit")
	parser.add_argument("--csv", action="store_true", help="print csv raw output")
	parser.add_argument("--iface", default="eth0", help="interface name")
	return parser.parse_args()



def sizeof_fmt(num, suffix="B"):
        """convert to human readable form"""

        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
                if abs(num) < 1000.0:
                        return "%3.1f %1s%s" % (num, unit, suffix)
                num /= 1000.0
        return "%.1f %1s%s" % (num, "Y", suffix)



def stats_tcp_read():
	"""read tcp stats from proc"""

	# https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git/tree/include/net/tcp_states.h	
	tran = [ \
		"padding", "TCP_ESTABLISHED", "TCP_SYN_SENT", "TCP_SYN_RECV", "TCP_FIN_WAIT1", "TCP_FIN_WAIT2",
		"TCP_TIME_WAIT", "TCP_CLOSE", "TCP_CLOSE_WAIT", "TCP_LAST_ACK", "TCP_LISTEN",
		"TCP_CLOSING", "TCP_NEW_SYN_RECV", "undefined1", "undefined2", "TCP_MAX_STATES"]

	data = []
	with open("/proc/net/tcp", "r") as ftmp:
		data += ftmp.readlines()[1:]
	with open("/proc/net/tcp6", "r") as ftmp:
		data += ftmp.readlines()[1:]

	stat_by_state = dict(zip(tran, [0 for x in range(len(tran))]))
	for line in data:
		state = tran[int(line.split()[3], 16)]
		stat_by_state[state] += 1

	logger.debug(stat_by_state)
	return stat_by_state



def stats_rxtx_read(iface):
	"""read rxtx stats from proc"""

	ftmp = open("/proc/net/dev", "r")
	for line in [x.strip() for x in ftmp.readlines()]:
		if line.startswith("%s:" % iface):
			break
		line = None

	if line:
		# face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
		#eth0: 76594958  122515    7    0    0     0          0         0 72115331  110248    0    0    0     0       0          0
		logger.debug(line)
		stats = { \
			"rx": dict(zip(["bytes", "packets", "errs", "drop", "fifo", "frame", "compressed", "multicast"], map(int, line.split()[1:8]))),
			"tx": dict(zip(["bytes", "packets", "errs", "drop", "fifo", "colls", "carrier", "compressed"], map(int, line.split()[9:16])))}
	else:
		logger.error("interface statistics not found")
		return False

	logger.debug(stats)
	return stats



def stats_diff(old, new, time):
	keys = old.keys()
	vals = [((new[x] - old[x])/time) for x in keys]
	return dict(zip(keys, vals))



def stats(iface, timespan, csv=False):
	# grab stats in timespan
	stats_rxtx_old = stats_rxtx_read(iface)
	time.sleep(timespan)
	stats_rxtx_new = stats_rxtx_read(iface)
	stats_tcp = stats_tcp_read()

	# postprocess
	## rxtx stats
	diff = { \
		"rx": stats_diff(stats_rxtx_old["rx"], stats_rxtx_new["rx"], timespan),
		"tx": stats_diff(stats_rxtx_old["tx"], stats_rxtx_new["tx"], timespan)}
	logger.debug(diff)

	## tcp stats group by statemachine states
	## active - action initiated by localhost, passive - action initiated by remote peer
	tcp_open_active = stats_tcp["TCP_SYN_SENT"]
	tcp_open_passive = sum([stats_tcp[x] for x in ["TCP_SYN_RECV", "TCP_NEW_SYN_RECV"]])
	tcp_close_active = sum([stats_tcp[x] for x in ["TCP_FIN_WAIT1", "TCP_FIN_WAIT2", "TCP_CLOSING", "TCP_TIME_WAIT"]])
	tcp_close_passive = sum([stats_tcp[x] for x in ["TCP_CLOSE_WAIT", "TCP_LAST_ACK"]])


	# generate output
	## iface rx/tx bits, bytes, packets
	## globalwide 4+6 tcp: opening active / passive | listen / established | closing active / passive
	if csv:
		ret = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % ( \
			8*diff["rx"]["bytes"], diff["rx"]["bytes"], diff["rx"]["packets"],
			8*diff["tx"]["bytes"], diff["tx"]["bytes"], diff["tx"]["packets"],
			tcp_open_active, tcp_open_passive, stats_tcp["TCP_LISTEN"], stats_tcp["TCP_ESTABLISHED"], tcp_close_active, tcp_close_passive)
	else:
		ret = "rx: %10s %10s %10s    tx: %10s %10s %10s    tcp: %4s/%4s | %4s/%4s | %4s/%4s" % ( \
			sizeof_fmt(8*diff["rx"]["bytes"], "b"),	sizeof_fmt(diff["rx"]["bytes"], "B"), sizeof_fmt(diff["rx"]["packets"], "p"),
			sizeof_fmt(8*diff["tx"]["bytes"], "b"),	sizeof_fmt(diff["tx"]["bytes"], "B"), sizeof_fmt(diff["tx"]["packets"], "p"),
			tcp_open_active, tcp_open_passive, stats_tcp["TCP_LISTEN"], stats_tcp["TCP_ESTABLISHED"], tcp_close_active, tcp_close_passive)

	return ret



def main():
	args = parse_arguments()
	if args.debug:
		logger.setLevel(logging.DEBUG)

	try:
		while True:
			print stats(args.iface, args.time, args.csv)
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	sys.exit(main())
