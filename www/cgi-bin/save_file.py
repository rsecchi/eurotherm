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


####### schedule command ####################
#def schedule_script(fname, units, ptype, control,
#	laid, cname, caddr, ccomp,
#	mtype="", height=""):
#	cmd = "at now <<< '%s %s %s %s %s %s %s %s %s %s %s > %s 2> %s'" % (script,
#		 fname, units, ptype, control, laid, cname, caddr, ccomp, 
#		mtype, height, logfile, logfile)
#
#	cmd1 = "/usr/bin/python3 %s %s %s %s %s %s %s %s %s %s %s" % (script,
#		 fname, units, ptype, control, laid, cname, caddr, ccomp, 
#		mtype, height)
#
#	cmd2 = "python3 %s %s %s %s %s %s %s %s %s %s %s > %s 2> %s" % (script,
#		 fname, units, ptype, control, laid, cname, caddr, ccomp, 
#		mtype, height, logfile, logfile)


def schedule_script(dxf_file, cfg_file):

	cmd = "/usr/bin/python3 %s %s %s" % (script, dxf_file, cfg_file)
	
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
	web_filename = get_filename(fid)
	config_filename = web_filename[:-3]+"cfg"
	###### Convert form into JSON ######

	form_data = dict()
	for key in form.keys():
		if key != 'filename':
			form_data[key] = form.getvalue(key)

	form_data['dxffile'] = web_filename
	form_data['cfgfile'] = config_filename

	# Convert the dictionary to a JSON string
	json_data = json.dumps(form_data, indent=4)

	cfg_file = open(config_filename,"w")
	cfg_file.write(json_data)
	cfg_file.close()
	# Output the JSON data
	

	# DXF settings
	#units = form.getvalue('units')
	#ptype = form.getvalue('ptype')

	## Smartpoints	
	#control = form.getvalue('control')

	## Air
	#mtype = form.getvalue('head')
	#mnt   = form.getvalue('inst')	
	#regtype = form.getvalue('regulator')
	#height = form.getvalue('height')

	## Client details
	#laid = form.getvalue('laid').replace(" ", "_")
	#cname = form.getvalue('cname').replace(" ", "_")
	#caddr = form.getvalue('caddr').replace(" ", "_")
	#ccomp = form.getvalue('ccomp').replace(" ", "_")

	#if mtype=='air':
	#	mtype = regtype + "_" + mnt
	

	fileitem =  form['filename']
	outfile = open(web_filename, 'wb')
	outfile.write(fileitem.file.read())
	
	schedule_script('"'+web_filename+'"', '"'+config_filename+'"')

	#schedule_script('"'+web_filename+'"', units, ptype, control, 
	#	laid, cname, caddr, ccomp,
	#	mtype, height)



ff = open(load_page, "r")
print(ff.read() % os.path.basename(web_filename))


#print(os.path.basename(form.getvalue("file")))


