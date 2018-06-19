#!/usr/bin/python
"""tg utils module"""

import datetime
import pyroute2
import re
import socket


def default_output_interface(family=socket.AF_INET):
	"""returns interface for first default route"""

	ipr = pyroute2.IPRoute()
	first_default_route = ipr.get_default_routes(family=family)[0]
	default_route_link = ipr.get_links(first_default_route.get_attr("RTA_OIF"))[0]
	return default_route_link.get_attr("IFLA_IFNAME")


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
