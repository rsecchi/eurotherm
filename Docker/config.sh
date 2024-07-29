#!/bin/bash

DIR="/usr/local/src/eurotherm/www"
	
cp $DIR/logo-leonardo-planner-cs-stable.png $DIR/logo-leonardo-planner.png

if [ "${MODE}" == "testing"  ]; then
	# commands to execute in testing case
	cp $DIR/logo-leonardo-planner-cs-testing.png $DIR/logo-leonardo-planner.png
	ARGS="-DTESTING"
fi

httpd-foreground $ARGS

