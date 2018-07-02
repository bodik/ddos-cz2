"""tg utils module"""

import datetime
import ipaddress
import pyroute2
import re
import struct
import socket



def default_output_interface(family=socket.AF_INET):
	"""returns interface for first default route"""

	ipr = pyroute2.IPRoute()
	first_default_route = ipr.get_default_routes(family=family)[0]
	default_route_link = ipr.get_links(first_default_route.get_attr("RTA_OIF"))[0]
	return default_route_link.get_attr("IFLA_IFNAME")



def interface_mac(iface_name):
	"""returns interfaces link address"""

	ipr = pyroute2.IPRoute()
	iface_index = ipr.link_lookup(ifname=iface_name)[0]
	iface_link = ipr.get_links(iface_index)[0]
	return iface_link.get_attr("IFLA_ADDRESS")



def interface_ip(iface_name, family=socket.AF_INET):
	""" return interfaces ip address"""

	ipr = pyroute2.IPRoute()
	iface_index = ipr.link_lookup(ifname=iface_name)[0]
	iface_addr = ipr.get_addr(family=family, index=iface_index)[0]
	return iface_addr.get_attr("IFA_ADDRESS")



def interface_gateway_ip(iface_name, family=socket.AF_INET):
	"""returns gateway address for interface"""

	ipr = pyroute2.IPRoute()
	iface_index = ipr.link_lookup(ifname=iface_name)[0]
	for route in ipr.get_routes(family=family):
		if route.get_attr("RTA_OIF") == iface_index and route.get_attr("RTA_GATEWAY"):
			return route.get_attr("RTA_GATEWAY")



def arping(ipaddr, iface_name):
	"""generates arp request on interface for ip address"""

	source_mac = bytes.fromhex(interface_mac(iface_name).replace(":", ""))
	source_address = interface_ip(iface_name)
	destination_mac = b"\xff\xff\xff\xff\xff\xff"
	destination_address = ipaddr

	# eth = dmac, smac, eth_type_protocol
	# arp = hardware type, protocol type, hardware address length, protocol address length, operation,
	#	source hardware address, source protocol address, destination hardware address, destination protcol address
	eth = struct.pack("!6s6sH", destination_mac, source_mac, 0x0806)
	arp = struct.pack("!HHBBH6s4s6s4s", 1, 0x0800, 6, 4, 1,\
		source_mac, socket.inet_aton(source_address), destination_mac, socket.inet_aton(destination_address))
	packet = eth + arp

	sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
	sock.bind((iface_name, 0))
	sock.send(packet)
	sock.close()



def ip_to_mac(ipaddr, iface_name):
	"""resolves link addres from address"""

	# TODO: ipv6 support
	# ensure record in cache
	arping(ipaddr, iface_name)

	# get record from cache
	ipr = pyroute2.IPRoute()
	neigh = ipr.get_neighbours(dst=ipaddr)[0]
	if neigh:
		return neigh.get_attr("NDA_LLADDR")

	return None



def trafgen_format_mac(mac):
	"""format mac address to trafgen bytes"""
	return ",".join(["0x%s" % x for x in mac.split(":")])



def trafgen_format_ip(ipaddr):
	"""format ip address to trafgen bytes"""

	if ipaddr.count(".") == 3:
		return ipaddr.replace(".", ",")

	if ipaddr.count(":") >= 2:
		return ",".join(["c16(0x%s)" % hextet for hextet in ipaddress.IPv6Address(ipaddr).exploded.split(":")])

	raise ValueError("invalid ipaddr")



def parse_time(data):
	"""parse time spec 1h2m3s to total seconds"""

	regex = re.compile(r"^((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s?)?$")
	parts = regex.match(data)
	if not parts:
		raise ValueError("invalid time")
	parts = parts.groupdict()
	time_params = {}
	for (name, param) in parts.items():
		if param:
			time_params[name] = int(param)
	return datetime.timedelta(**time_params).total_seconds()
