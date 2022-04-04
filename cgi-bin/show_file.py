#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess


from conf import *


if os.path.exists(lock_name):
	print("Content-Type: text/html\n")
	ff = open(load_page, "r")
	print(ff.read())

	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print("<pre>")
		print(flog.read())	
		print("</pre>")
	
else:
	print("Content-Type: text/html\n")
	#print("Location: http://eurotherm.ddns.net/done.html\n")

	ff = open(done_page, "r")
	print(ff.read())
	if os.path.exists(web_file):
		print('<p><a href="' + web_output + '" download>Scarica DXF</a></p>')

	if os.path.exists(web_xls):
		print('<p><a href="' + xls_output + '" download>Scarica XLS</a></p>')

	print("</div></body></html>")
