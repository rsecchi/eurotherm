#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess
import fcntl

from variables import *


cgi_root     = "/var/www/cgi-bin/eurotherm/"
web_filename = "/var/apache_tmp/input.dxf"
lock_name    = "/var/apache_tmp/eurotherm.lock"
script       = "/var/www/cgi-bin/eurotherm/leonardo.py"
logfile      = "/var/apache_tmp/log"


####### schedule command ####################
def schedule_script(fname, units):


	cmd = "at now <<< '%s %s %s > %s 2> %s'" % (script, fname, units, logfile, logfile) 
	subprocess.Popen(['/bin/bash', '-c', cmd])

#############################################

cgitb.enable()
form = cgi.FieldStorage()


print("Content-Type: text/html\n")
lock = open(lock_name, "w")

if not os.path.exists(lock_name):

	ff = open(cgi_root + "web_iface/loading.html", "r")
	print(ff.read())

	fileitem =  form['filename']
	units = form.getvalue('units')
	outfile = open(web_filename, 'wb')
	outfile.write(fileitem.file.read())
	schedule_script(web_filename, units)

except:
	print("<p>System busy, try in a few moments</p>")



