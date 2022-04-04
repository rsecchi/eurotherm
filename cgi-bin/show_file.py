#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"
from conf import *

if os.path.exists(lock_name):

	# Show progress of calculation
	print("Content-Type: text/html\n")
	ff = open(load_page, "r")
	print(ff.read())

	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print("<pre>")
		print(flog.read())	
		print("</pre>")
	
else:

	# Show webpage with results
	print("Content-Type: text/html\n")
	ff = open(done_page, "r")
	print(ff.read())

	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print('<div class="section">')
		print("<pre>")
		print(flog.read())	
		print("</pre>")
		print("</div>")

	print("</body>")
	print("</html>")

