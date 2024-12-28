#!/usr/bin/python3 -u

import cgi, os, sys, json
import cgitb
import html_elems

cgitb.enable()

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"

from conf import load_page_ita, done_page_ita, load_page_eng, done_page_eng
from conf import lock_name, logfile, settings_path, settings_file


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

	# Show webpage with results
	print("Cache-Control: no-store, no-cache, must-revalidate")
	print("Pragma: no-cache")
	print("Expires: 0")
	print("Content-Type: text/html\n")
	ff = open(done_page, "r")
	print(ff.read())

	if len(form.keys()) > 1:
		# Save the options
		with open(settings_file, "w") as f:
			json.dump({key: form.getvalue(key) for key in form.keys()},
					  f, indent=4)


	if os.path.exists(settings_file):
		os.remove(settings_file)

	sys.path.append(settings_path)
	from settings import Config

	section = html_elems.Section("Options")

	for key, value in Config.__dict__.items():
		if not key.startswith("__"):
			section.add(key, value)

	section.print()

print("</body></html>")
