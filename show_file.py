#!/usr/bin/python3 -u

import cgi, os, sys
import cgitb
import time
import subprocess


lock_name = "/var/apache_tmp/eurotherm.lock"
cgi_root = "/var/www/cgi-bin/eurotherm/"



print("Content-Type: text/html\n")

if os.path.exists(lock_name):
	ff = open(cgi_root + "web_iface/loading.html", "r")
	print(ff.read())
	print(

