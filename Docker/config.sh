#!/bin/bash

DIR="/usr/local/src/eurotherm/www"
	
cp $DIR/logo-leonardo-planner-1.png $DIR/logo-leonardo-planner.png

if [ "${MODE}" == "testing"  ]; then
	cp $DIR/logo-leonardo-planner-testing.png $DIR/logo-leonardo-planner.png
fi

httpd-foreground

