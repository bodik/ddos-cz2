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



def stats_read(iface):
	"""read stats from proc"""

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
	stats_old = stats_read(iface)
	time.sleep(timespan)
	stats_new = stats_read(iface)

	diff = { \
		"rx": stats_diff(stats_old["rx"], stats_new["rx"], timespan),
		"tx": stats_diff(stats_old["tx"], stats_new["tx"], timespan)}
	logger.debug(diff)

	if csv:
		ret = "%s,%s,%s,%s,%s,%s,%s" % ( \
			iface,
			8*diff["rx"]["bytes"], diff["rx"]["bytes"], diff["rx"]["packets"],
			8*diff["tx"]["bytes"], diff["tx"]["bytes"], diff["tx"]["packets"])
	else:
		ret = "%s    rx: %10s %10s %10s    tx: %10s %10s %10s" % ( \
			iface,
			sizeof_fmt(8*diff["rx"]["bytes"], "b"),	sizeof_fmt(diff["rx"]["bytes"], "B"), sizeof_fmt(diff["rx"]["packets"], "p"),
			sizeof_fmt(8*diff["tx"]["bytes"], "b"),	sizeof_fmt(diff["tx"]["bytes"], "B"), sizeof_fmt(diff["tx"]["packets"], "p"))

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
