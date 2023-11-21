import os, json
from subprocess import Popen
import subprocess

cfg = {
    "ptype": "55",
    "regulator": "dehum",
    "inst": "vert",
    "units": "auto",
    "caddr": "",
    "cname": "",
    "ccomp": "",
    "file": "",
    "control": "reg",
    "height": "2.7",
    "laid": "without",
    "head": "air",
    "outfile": "",
    "cfgfile": "config.cfg",
    "infile": "",
    "lock_name": "/var/spool/eurotherm/eurotherm.lock"
}

# Get the current working directory
current_directory = os.getcwd()
print("Current Working Directory:", current_directory)

# Change to the parent directory
parent_directory = os.path.dirname(current_directory)
os.chdir(parent_directory)

# Verify the change
updated_directory = os.getcwd()
print("Updated Working Directory:", updated_directory)


for file in sorted(os.listdir("reg_tests")):
	filename = file[:-4]
	extension = file[-4:]
	if file[:4] == "test"  and extension == ".dxf":
		cfg["file"] = file
		cfg["infile"] = file
		cfg["outfile"] = "LEO_" + file
		print(file)
		data = json.dumps(cfg, indent=4)
		cfgfile = open("reg_tests/config.cfg", "w")
		cfgfile.write(data)
		cfgfile.close()
		process = Popen(['/usr/bin/python3', 'leonardo.py', 'reg_tests/config.cfg'], stdout=subprocess.PIPE, text=True)
		print(process.communicate()[0])
		


