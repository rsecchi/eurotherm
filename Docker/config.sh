#!/bin/bash

DIR="/usr/local/src/eurotherm/www"

if [ "${MODE}" == "testing"  ]; then
	ln -sf $DIR/logo-leonardo-planner-1.png $DIR/logo-leonardo-planner.png
else
	ln -sf $DIR/logo-leonardo-planner-testing.png $DIR/logo-leonardo-planner.png
fi

httpd-foreground

