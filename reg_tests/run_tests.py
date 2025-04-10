import os, json
from subprocess import Popen
import subprocess
import shutil

cfg = {
    "ptype": "55",
    "regulator": "dehum",
    "inst": "vert",
    "units": "auto",
    "caddr": "",
    "cname": "",
    "ccomp": "",
    "file": "test.dxf",
    "infile": "test.dxf",
    "control": "reg",
	"lang": "eng",
    "height": "2.7",
    "laid": "without",
    "head": "air",
    "outfile": "",
	"target": "100",
    "cfgfile": "config.cfg",
    "lock_name": "/var/spool/eurotherm/eurotherm.lock"
}


for file in sorted(os.listdir("reg_tests")):
	filename = file[:-4]
	extension = file[-4:]
	if file[:4] == "test"  and extension == ".dxf":

		#copy to spool directory
		shutil.copy("reg_tests/" + file, "/var/spool/eurotherm/test.dxf")

		cfg["outfile"] = "LEO_" + file
		print(file)
		data = json.dumps(cfg, indent=4)
		cfgfile = open("reg_tests/config.cfg", "w")
		cfgfile.write(data)
		cfgfile.close()
		process = Popen([
			'/bin/sh', 
			'run_leo_main.sh',
			'reg_tests/config.cfg'],
			stdout=subprocess.PIPE, text=True)
		print(process.communicate()[0])
		


