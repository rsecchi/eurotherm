import os
import json
from subprocess import Popen
import subprocess

spool_dir = "/var/spool/eurotherm/"

cfg = {
    "laid": "without",
    "file": "",
    "inst": "vert",
    "control": "reg",
    "height": "2.7",
    "units": "auto",
    "head": "air",
    "ptype": "35",
    "cname": "",
    "regulator": "dehum_int",
    "caddr": "",
    "ccomp": "",
    "lang": "ita",
    "outfile": "",
    "cfgfile": "config.cfg",
    "infile": "",
    "lock_name": "/var/spool/eurotherm/eurotherm.lock"
}


for file in sorted(os.listdir(spool_dir)):
	print(file)
	
	if not file[:4] == "test":
		continue

	filename = file[:-4]
	cfg["file"] = file
	cfg["infile"] = file
	cfg["outfile"] = "LEO_" + file
 
	data = json.dumps(cfg, indent=4)
	print(data)

	cfgfile = open(spool_dir + "config.cfg", "w")
	cfgfile.write(data)
	cfgfile.close()
	process = Popen(['/usr/bin/bash', 'run_leo_main.sh', 
			spool_dir + 'config.cfg'], stdout=subprocess.PIPE, text=True)
	print(process.communicate()[0])

# for file in sorted(os.listdir("reg_tests2")):
# 	filename = file[:-4]
# 	extension = file[-4:]
# 	if file[:4] == "test"  and extension == ".dxf":
# 		cfg["file"] = file
# 		cfg["infile"] = file
# 		cfg["outfile"] = "LEO_" + file
# 		print(file)
# 		data = json.dumps(cfg, indent=4)
# 		cfgfile = open("reg_tests/config.cfg", "w")
# 		cfgfile.write(data)
# 		cfgfile.close()
# 		process = Popen(['/usr/bin/python3', 'src/leo_main.py', '../reg_tests/config.cfg'], stdout=subprocess.PIPE, text=True)
# 		print(process.communicate()[0])
		


