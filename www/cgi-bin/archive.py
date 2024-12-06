#!/usr/bin/python3 -u

import cgi, os
import glob
import cgitb
import time

cgitb.enable()

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"
from conf import *


form = cgi.FieldStorage()
lang = form.getvalue("lang")
load_page = load_page_ita
done_page = done_page_ita
if lang=="eng":
	load_page = load_page_eng
	done_page = done_page_eng


if os.path.exists(lock_name):

	# Show progress of calculation
	print("Cache-Control: no-store, no-cache, must-revalidate")
	print("Pragma: no-cache")
	print("Expires: 0")
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
	print("Cache-Control: no-store, no-cache, must-revalidate")
	print("Pragma: no-cache")
	print("Expires: 0")
	print("Content-Type: text/html\n")
	ff = open(done_page, "r")
	print(ff.read())

	extensions = [".zip", ".txt", ".xlsx", ".dat", ".doc", ".rep",
						".cfg", "__in__.dxf"]

	if "delete" in form.keys():
		strval = form.getvalue("delete")
		del_file = tmp + strval[1:-1]
		if (os.path.exists(del_file)):
			os.remove(del_file)
			for ext in extensions:
				ff = del_file[:-4] + ext
				if os.path.exists(ff):
					os.remove(ff)

	print('<div class="section">')
	if lang == "ita":
		print('<h4>File dispobili sul server</h4>')
	else:
		print('<h4>Files available on server</h4>')
		
	print('<ul>')

	files = list(filter(os.path.isfile, glob.glob(tmp + "*.dxf")))
	files.sort(key=lambda x: os.path.getmtime(x), reverse=True)


	for f in files:
		if f[-10:] == "__in__.dxf":
			continue
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

