#!/usr/bin/python3

import argparse
import logging
from scapy.all import *
import sys

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(message)s')



def expand(x):
	yield x
	while x.payload:
		x = x.payload
		yield x



def display(packets):
	for packet in packets:
		try:
			packet = Ether(packet.load)
		except:
			pass

		for layer in expand(packet):
			for field in layer.fields:
				if layer.name == "Raw":
					print("%s: %s" % ("Raw.load", repr(layer.load)))
				elif (layer.name == "TCP") and (field == "flags"):
					print("%s.%s: %s [%s]" % (layer.name, field, layer.flags, layer.sprintf('%TCP.flags%')))
				else:
					print("%s.%s: %s" % (layer.name, field, layer.fields[field]))
	return 0



def summary(packets):
	print("scapy_display.summary.count: %d" % len(packets))
	return 0



def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("inputfile", help="filename")
	args = parser.parse_args()

	packets = rdpcap(args.inputfile)
	display(packets)
	summary(packets)


if __name__ == "__main__":
	sys.exit(main())
