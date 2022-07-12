#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess
import fcntl


print("Content-Type: text/html\n")
cgitb.enable()
form = cgi.FieldStorage()

from conf import *


####### schedule command ####################
def schedule_script(fname, units, ptype, mtype="", height=""):
	cmd = "at now <<< '%s %s %s %s %s %s > %s 2> %s'" % (script,
		 fname, units, ptype, mtype, height, logfile, logfile)
	subprocess.Popen(['/bin/bash', '-c', cmd])
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

	# Receive settings
	fileitem =  form['filename']
	units = form.getvalue('units')
	ptype = form.getvalue('ptype')
	
	mtype = form.getvalue('head')
	
	regtype = form.getvalue('regulator')
	height = form.getvalue('height')

	if (mtype=='cold'):
		mtype = regtype

	outfile = open(web_filename, 'wb')
	outfile.write(fileitem.file.read())
	schedule_script('"'+web_filename+'"', units, ptype, mtype, height)


ff = open(load_page, "r")
print(ff.read())


#print(os.path.basename(form.getvalue("file")))

