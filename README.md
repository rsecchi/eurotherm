# Eurotherm Planner

Main Python script executing the calculation. It can be called as a command line as follow:
```
./leonardo.py <filename> <units>
```
where the filename is the DXF inputs and units it is the units used in the DXF in cm or "auto"

# Installing the web interface

> We assume to extract the files in /usr/local/scr 
```
cd /usr/local/src
git clone https://github.com/rsecchi/eurotherm.git
```

> The following Virtual Host is added to the Apache configuration: 

* The directory /www is used as DocumentRoot
* The directory /cgi-bin is used as CGI directory
* The apache user (www-data) should be allowed to writhe in the spool directory (/var/spool/eurotherm)


```

<VirtualHost *:80>
    ServerAdmin r.secchi@gmail.com
    DocumentRoot /usr/local/src/eurotherm
    Alias /output/ /var/spool/eurotherm/

	ScriptAlias /cgi-bin/ /usr/local/src/eurotherm/cgi-bin/
	<Directory /var/www/cgi-bin>
	    Options ExecCGI
    	SetHandler cgi-script
	</Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    Options ExecCGI Includes MultiViews Indexes SymLinksIfOwnerMatch
    AddHandler cgi-script .py

</VirtualHost>
```

> Note that access to the above directories should be allowed the main configuration.

> Edit the file cgi-bin/conf.py to point to the directories:

* The temporary spool directory is referenced by "tmp"
* The package directory is referenced by "local_dir"

