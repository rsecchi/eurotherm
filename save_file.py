#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess

####### schedule command ####################
def schedule_script(fname, units):

	script = "/var/www/cgi-bin/eurotherm/leonardo.py"
	logfile = "/var/apache_tmp/log"

	cmd = "at now <<< '%s %s %s > %s 2> %s'" % (script, fname, units, logfile, logfile) 
	subprocess.Popen(['/bin/bash', '-c', cmd])

#############################################

web_filename = '/var/apache_tmp/input.dxf'

cgitb.enable()
form = cgi.FieldStorage()

print("""\
Content-Type: text/html\n
<html>
<body>
<p>Leonardo Planner sta elaborando il vostro progetto</p>
<p>Attendere prego</p>
</body>
</html>
""")

fileitem =  form['filename']
units = form.getvalue('units')


outfile = open(web_filename, 'wb')
outfile.write(fileitem.file.read())

schedule_script(web_filename, units)

