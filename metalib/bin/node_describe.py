#!/usr/bin/python3

import json
import subprocess

facts = json.loads(subprocess.check_output(["facter", "--json"]).decode("UTF-8"))
node_description = { \
	"fqdn": facts["fqdn"],
	"lsbdistdescription": facts["lsbdistdescription"],
	"memorysize": facts["memorysize"],
	"physicalprocessorcount": facts["physicalprocessorcount"],
	"processorcount": facts["processorcount"],
	"processor0": facts["processor0"],
	"uname": subprocess.check_output(["uname", "-a"]).decode("UTF-8"),
	"virtual": facts["virtual"]}

print(json.dumps(node_description, indent=4, sort_keys=True))
