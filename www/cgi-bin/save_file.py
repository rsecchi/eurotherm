#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
from subprocess import Popen, STDOUT, PIPE, run
import fcntl
import json


print("Content-Type: text/html\n")
cgitb.enable()
form = cgi.FieldStorage()

from conf import *


def start_script(cfg_file):

	cmd = "/usr/bin/python3 %s %s" % (script, cfg_file)
	
	# The following code is from:
	# https://mail.python.org/pipermail/python-list/2001-March/085332.html

	sys.stdout.flush()
	sys.stderr.flush()

	if os.fork() == 0:
		fileout = os.open(logfile, os.O_CREAT|os.O_WRONLY|os.O_TRUNC)
		os.dup2(fileout, sys.stdout.fileno())
		os.dup2(fileout, sys.stderr.fileno())
		os.close(fileout)

		devnull = os.open("/dev/null", os.O_RDONLY)
		os.dup2(devnull, sys.stdin.fileno())
		os.close(devnull)

		Popen(['/bin/bash', '-c', cmd])
		exit(0)

#############################################


def get_filename(fid):
	bname = fid[:-4]
	for i in range(1,100):
		ff = tmp + bname + "_leo_%02d.dxf" % i
		if (not os.path.exists(ff)):
			return ff


if not os.path.exists(lock_name):

	fid = form.getvalue("file")
	output_filename = get_filename(fid)
	config_filename = web_filename[:-3]+"cfg"

	###### Convert form into JSON ######
	form_data = dict()
	for key in form.keys():
		if key != 'filename':
			form_data[key] = form.getvalue(key)

	form_data['outfile'] = output_filename
	form_data['cfgfile'] = config_filename

	# Create config file using a JSON string
	json_data = json.dumps(form_data, indent=4)
	cfg_file = open(config_filename,"w")
	cfg_file.write(json_data)
	cfg_file.close()

	# Create input filename
	fileitem =  form['filename']
	outfile = open(web_filename, 'wb')
	outfile.write(fileitem.file.read())
	outfile.close()
	
	start_script('"'+config_filename+'"')



ff = open(load_page, "r")
print(ff.read() % os.path.basename(output_filename))




