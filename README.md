# Eurotherm Planner

Maini Python script executing the calculation. It can be called as a command line as follow:
```
./leonardo.py <filename> <units>
```
where the filename is the DXF inputs and units it is the units used in the DXF in cm or "auto"

# Installing the web interface

>The directory web\_frontend should be used as DocumentRoot

>The directory cgi-bin should be linked to the CGI directory

>Example of Apache configuration

```
ScriptAlias /cgi-bin/ /var/www/cgi-bin/
<Directory /var/www/cgi-bin>
    Options ExecCGI
    SetHandler cgi-script
</Directory>

<VirtualHost *:80>
    ServerAdmin r.secchi@gmail.com
    DocumentRoot /var/www/eurotherm

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    Options ExecCGI Includes MultiViews Indexes SymLinksIfOwnerMatch
    AddHandler cgi-script .py

</VirtualHost>
```

```
ln -s $PWD/web_frontend /var/www/eurotherm
```


