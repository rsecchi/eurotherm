#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess
import re

cgitb.enable()

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

	form = cgi.FieldStorage()	

	# Show webpage with results
	print("Content-Type: text/html\n")
	ff = open(done_page, "r")
	print(ff.read())

	print('<div class="section">')
	print('    <h4>Risultati calcolo tecnico</h4>')
	print('    <p><a href="/output/output.dxf" download>Scarica DXF</a></p>')
	print('    <p><a href="/output/output.xlsx" download>Scarica XLS</a></p>')
	print('</div>')

	fin = open(tmp + "output.txt", "r")
	print(fin.read())


	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print('<div class="section">')
		print('<h4>Log file</h4>')
		print("<pre>")
		print(flog.read())	
		print("</pre>")
		print("</div>")


	print("</body>")
	print("</html>")

