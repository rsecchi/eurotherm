#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb

cgitb.enable()

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"

from conf import load_page_ita, done_page_ita, load_page_eng, done_page_eng
from conf import lock_name, logfile, settings_path


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

	print("<pre>")
	print("Settings:")
	print(settings_path)
	print("</pre>")

	sys.path.append(settings_path)
	from settings import Config
	print(Config.__dict__)

print("</body></html>")
