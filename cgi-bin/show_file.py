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

	print("<p>");
	if "delete" in form.keys():
		strval = form.getvalue("delete")
		del_file = tmp + strval[1:-1]
		if (os.path.exists(del_file)):
			print("file exists!!")
			os.remove(del_file)
			os.remove(del_file[:-4] + ".txt")

	print("</p>");

	print('<div class="section">')
	print('<h4>File dispobili sul server</h4>')
	print('<ul>')
	floc = os.listdir(tmp)
	rule = re.compile(".*_leo_.*dxf$")
	files = list(filter(rule.match, floc))
	files.sort()

	for f in files:
		path = tmp + f
		t = os.path.getmtime(path)
		href_dxf = '"/output/' + f + '"'
		href_xls = '"/output/' + f[:-4] + '.xlsx"'
		href_log = '"/output/' + f[:-4] + '.txt"'
		rule = re.compile("^.*_leo")
		fname = rule.match(f).group(0)
		rule = re.search("_leo_.*",f)
			
		tag = rule.group(0)
		print('<li>')
		print('<elem>', fname[:-4], '</elem>')
		print('<filetag>', tag[5:7], '</filetag>')
		print('<refs>')
		print('<ref><a href=',href_dxf,' download>[DXF]</a></ref>')
		print('<ref><a href=',href_xls,' download>[XLS]</a></ref>')
		print('<ref><a href=',href_log,' download>[LOG]</a></ref>')
		print('</refs>')
		print('<date>', time.ctime(t),'</date>')
		print('<ref><a href="/cgi-bin/show_file.py?delete=\''+f, end='')
		print('\'">[x]</a><ref>')

		print('</li>')

	print('</ul>')
	print('</div>')

	if os.path.exists(logfile):
		flog = open(logfile, "r")
		print('<div class="section">')
		print('<h4>Relazione ultimo calcolo</h4>')
		print("<pre>")
		print(flog.read())	
		print("</pre>")
		print("</div>")


	print("</body>")
	print("</html>")

