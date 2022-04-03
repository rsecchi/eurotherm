#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess


from conf import *

print("Content-Type: text/html\n")

if os.path.exists(lock_name):
	ff = open(load_page, "r")
	print(ff.read())

	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print("<pre>")
		print(flog.read())	
		print("</pre>")
	
else:
	if os.path.exists(web_file):
		print("<p>", lock_name)
		print('<a href="' + web_output + '" download>Scarica DXF</a>')
		print("</p>")

	if os.path.exists(web_xls):
		print("<p>")
		print('<a href="' + xls_output + '" download>Scarica XLS</a>')
		print("</p>")
