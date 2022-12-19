#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess
import re


def update_link(basename, ftype):
	global tmp

	output_ftype = tmp + "output." + ftype
	filename_ftype = tmp + basename + "." + ftype

	if (os.path.islink(output_ftype)):
		os.unlink(output_ftype)
	os.symlink(filename_ftype, output_ftype)


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

	ftypes = ["dxf", "txt", "xlsx", "dat", "doc"]

	output = {}
	for ftype in ftypes:
		output[ftype] = tmp + "output." + ftype

	if (not filename == None):
		basename = filename[:-4]
		for ftype in ftypes:
			update_link(basename, ftype)


	print('<div class="section">')
	print('<h4>Risultati calcolo tecnico</h4><ul>')
	fname = {}
	for ftype in ftypes:
		if not os.path.exists(output[ftype]):
			continue
		ff = os.path.basename(os.readlink(output[ftype]))
		print('\t<li><span>Scarica file %s</span>' % ftype, end="")
		print('[<a href="/output/%s" download>%s</a>]</li>' % (ff, ff)) 

	print('</ul></div>')

	if (os.path.exists(output["txt"])):
		fin = open(output["txt"], "r")
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

