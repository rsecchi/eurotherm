#!/usr/bin/python3 -u

import cgi, os, sys
import glob
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

	if "delete" in form.keys():
		strval = form.getvalue("delete")
		del_file = tmp + strval[1:-1]
		if (os.path.exists(del_file)):
			os.remove(del_file)
			for ext in [".txt", ".xlsx", ".dat", ".doc", "png"]:
				ff = del_file[:-4] + ext
				if os.path.exists(ff):
					os.remove(ff)

	print('<div class="section">')
	print('<h4>File dispobili sul server</h4>')
	print('<ul>')

	files = list(filter(os.path.isfile, glob.glob(tmp + "*.dxf")))
	files.sort(key=lambda x: os.path.getmtime(x), reverse=True)


	for f in files:
		t = os.path.getmtime(f)
		href_dxf = '"/output/' + f + '"'
		href_xls = '"/output/' + f[:-4] + '.xlsx"'
		href_log = '"/output/' + f[:-4] + '.txt"'


		fname = os.path.basename(f)

		if (fname == "input.dxf" or fname == "output.dxf"):
			continue

		print('<li onclick="show_selected(this)">')
		print('<ref><a href="archive.py?delete=\''+fname, end='')
		print('\'">[x]</a><ref>')
		print('<elem>'+fname+'</elem>')
		#print('<refs>')
		#print('<ref><a href='+href_dxf+' download>[DXF]</a></ref>')
		#print('<ref><a href='+href_xls+' download>[XLS]</a></ref>')
		#print('<ref><a href='+href_log+' download>[LOG]</a></ref>')
		#print('</refs>')
		print('<date>', time.ctime(t),'</date>')

		print('</li>')

	print('</ul>')
	print('</div>')


	print("</body>")
	print("</html>")

