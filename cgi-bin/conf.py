
tmp          = "/var/apache_tmp/"
cgi_root     = "/var/www/cgi-bin/eurotherm/"
web_root     = "/var/www/eurotherm/"

web_filename = tmp + "input.dxf"
web_file     = tmp + "input_leo.dxf"
web_xls      = tmp + "input.xlsx"
lock_name    = tmp + "eurotherm.lock"
logfile      = tmp + "log"

script       = cgi_root + "leonardo.py"
load_page    = web_root + "loading.html"

web_output   = "http://eurotherm.ddns.net/output/input_leo.dxf"
xls_output   = "http://eurotherm.ddns.net/output/input.xlsx"

