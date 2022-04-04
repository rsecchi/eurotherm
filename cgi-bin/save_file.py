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
def schedule_script(fname, units):
	cmd = "at now <<< '%s %s %s > %s 2> %s'" % (script, fname, units, logfile, logfile) 
	subprocess.Popen(['/bin/bash', '-c', cmd])

#############################################

if not os.path.exists(lock_name):

	fileitem =  form['filename']
	units = form.getvalue('units')
	outfile = open(web_filename, 'wb')
	outfile.write(fileitem.file.read())
	schedule_script(web_filename, units)


ff = open(load_page, "r")
print(ff.read())

