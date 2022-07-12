#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess
import re

cgitb.enable()

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"
from conf import *
	
form = cgi.FieldStorage()	
filename = form.getvalue("filename")

if os.path.exists(lock_name):

	# Show progress of calculation
	print("Content-Type: text/html\n")
	ff = open(load_page, "r")
	print(ff.read() % filename)

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

	output_dxf = tmp + "output.dxf"
	output_xls = tmp + "output.xlsx"
	output_txt = tmp + "output.txt"

	if (not filename == None):
		# Creates new dynamic links if a filename is passed
		filename_dxf = tmp + filename
		filename_xls = tmp + filename[:-4] + ".xlsx"
		filename_txt = tmp + filename[:-4] + ".txt"

		if (os.path.islink(output_dxf)):
			os.unlink(output_dxf)

		if (os.path.islink(output_xls)):
			os.unlink(output_xls)

		if (os.path.islink(output_txt)):
			os.unlink(output_txt)

		os.symlink(filename_dxf, output_dxf)
		os.symlink(filename_xls, output_xls)
		os.symlink(filename_txt, output_txt)
		
	filename_dxf = os.path.basename(os.readlink(output_dxf))
	filename_xls = os.path.basename(os.readlink(output_xls))
	filename_txt = os.path.basename(os.readlink(output_txt))


	# Now show the outputs
	print('<div class="section">')
	print('<h4>Risultati calcolo tecnico</h4><ul>')
	print('    <li>Scarica DXF elaborato [<a href="/output/%s" download>%s</a>]</li>' 
		% (filename_dxf, filename_dxf))
	print('    <li>Scarica XLS elaborato [<a href="/output/%s" download>%s</a>]</li>' 
		% (filename_xls, filename_xls))
	print('</ul></div>')

	fin = open(output_txt, "r")
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

