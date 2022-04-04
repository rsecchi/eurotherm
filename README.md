# Eurotherm Planner

Maini Python script executing the calculation. It can be called as a command line as follow:
```
./leonardo.py <filename> <units>
```
where the filename is the DXF inputs and units it is the units used in the DXF in cm or "auto"

# Installing the web interface

> We assume to extract the  
```
cd /usr/local/src
git clone https://github.com/rsecchi/eurotherm.git
```

> 

```
ScriptAlias /cgi-bin/ /usr/local/src/eurotherm/cgi-bin/
<Directory /var/www/cgi-bin>
    Options ExecCGI
    SetHandler cgi-script
</Directory>

<VirtualHost *:80>
    ServerAdmin r.secchi@gmail.com
    DocumentRoot /usr/local/src/eurotherm
    Alias /output/ /var/spool/eurotherm/

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    Options ExecCGI Includes MultiViews Indexes SymLinksIfOwnerMatch
    AddHandler cgi-script .py

</VirtualHost>
```

* The directory /www is used as DocumentRoot
* The directory /cgi-bin is used as CGI directory
* The apache user (www-data) should have access to the spool directort (/var/spool/eurotherm)


> Note that ExecGCI and FollowSymlinks should be allowed in the main configuration, in
in the site configuration and in .htaccess if present in the CGI directory.

* Edit the file cgi-bin/conf.py to point the CGI bin directory, the web directory and the temp dire
ctory to point to the chosen directories

