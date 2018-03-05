#!/usr/bin/python

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



def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("inputfile", help="filename")
	args = parser.parse_args()

	for packet in rdpcap(args.inputfile):
		for layer in list(expand(Ether(packet.load))):
			for field in layer.fields:
				if layer.name == "Raw":
					layer.display()
				else:
					print "%s.%s: %s" % (layer.name, field, layer.fields[field])

	return 0

if __name__ == "__main__":
	sys.exit(main())
