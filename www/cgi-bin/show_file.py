#!/usr/bin/python3 -u

import cgi, os
import cgitb
# import zipfile


def update_link(basename, ftype):
	global tmp

	output_ftype = tmp + "output" + ftype
	filename_ftype = tmp + basename + ftype

	if (os.path.islink(output_ftype)):
		os.unlink(output_ftype)

	os.symlink(filename_ftype, output_ftype)

	return filename_ftype	
	


cgitb.enable()

local_dir = os.path.dirname(os.path.realpath(__file__)) + "/../"
from conf import *
	
form = cgi.FieldStorage()	
filename = form.getvalue("filename")

lang = form.getvalue("lang")
load_page = load_page_ita
if lang == "eng":
	load_page = load_page_eng

done_page = done_page_ita
if lang == "eng":
	done_page = done_page_eng

if os.path.exists(lock_name):

	# Show progress of calculation
	print("Cache-Control: no-store, no-cache, must-revalidate")
	print("Pragma: no-cache")
	print("Expires: 0")
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
	print("Cache-Control: no-store, no-cache, must-revalidate")
	print("Pragma: no-cache")
	print("Expires: 0")
	print("Content-Type: text/html\n")
	ff = open(done_page, "r")
	print(ff.read())

	ftypes = [".dxf", ".txt", ".xlsx", ".dat", ".doc", ".rep", ".png"]
	if os.environ.get("MODE") == "testing":
		ftypes.append(".cfg")
		ftypes.append("__in__.dxf")

	output = {}
	for ftype in ftypes:
		output[ftype] = tmp + "output" + ftype

	ziplist = list()
	if (not filename == None):
		# link generated outputfile
		basename = filename[:-4]
		for ftype in ftypes:
			update_link(basename, ftype)
			if os.path.exists(tmp+basename+ftype):
				ziplist.append(tmp+basename+ftype)

		# make zipfile in testing
		# if os.environ.get("MODE") == "testing":
		# zipname = tmp + basename + ".zip"
		# if not os.path.exists(zipname):
		# 	zipf = zipfile.ZipFile(zipname, "w")
		# 	for zf in ziplist:
		# 		zout = os.path.basename(zf)
		# 		zipf.write(zf, basename+"/"+zout)
		# ftypes.append(".zip")
		# output[".zip"] = tmp + "output" + ".zip"
		# update_link(basename, ".zip")

	print('<div class="section_dup">')

	print('<div class="file_list">')
	if lang == "ita":
		print('<h4>Risultati calcolo tecnico</h4><ul>')
	else:
		print('<h4>Results of elaboration</h4><ul>')


	fname = {}
	for ftype in ftypes:

		if ftype == ".rep":
			continue

		if not os.path.exists(output[ftype]):
			continue
		ff = os.path.basename(os.readlink(output[ftype]))
		if lang=="ita":
			print('\t<li><span>Scarica file %s</span>' % ftype, end="")
		else:
			print('\t<li><span>Download file %s</span>' % ftype, end="")
		print('[<a href="/output/%s" download>%s</a>]</li>' % (ff, ff)) 
	

	print('</ul></div>')


	if os.path.exists(output[".png"]):
		fimage = open(output[".txt"], "r")
		ff = os.path.basename(os.readlink(output[".png"]))
		print('<div class="florplan" >')
		# <img src="img_girl.jpg" alt="Girl in a jacket">
		if lang=="ita":
			print('<h4>Pianta</h4>')
		else:
			print('<h4>Floor plan</h4>')
		print('<div style="text-align: center;" >')
		print('<img src="/output/%s" width="500">' % ff) 
		print("</div></div>")

	print("</div>")

	if os.path.exists(output[".rep"]):
		fin = open(output[".rep"], "r")
		print(fin.read())

	if os.path.exists(output[".txt"]):
		fin = open(output[".txt"], "r")
		print("<div class='section'>")
		if lang=="ita":
			print('<h4>Relazione Calcolo</h4>')
		else:
			print('<h4>Computation Report</h4>')

		for line in fin:
			if len(line)>1 and line[-2]=="@":
				print("<pre style='background-color: yellow;'>")
				print(line[:-2], end="")
			else:
				print("<pre>")
				print(line, end="")
			print("</pre>")
		print("</div>")

	#if os.path.exists(logfile) and os.environ.get("MODE") == "testing":
	#	flog = open(logfile, "r")
	#	print('<div class="section">')
	#	print('<h4>Log file</h4>')
	#	print("<pre>")
	#	print(flog.read())	
	#	print("</pre>")
	#	print("</div>")


	print("</body>")
	print("</html>")

