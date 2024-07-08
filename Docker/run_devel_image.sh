#!/bin/bash

if [ ! -d "$ARCHIVE" ]; then
	echo "Please provide the archive location by setting the variable ARCHIVE"
	exit
fi

if [ ! -d "$SOURCES" ]; then
	echo "Please provide the sources location by setting the variable SOURCES"
	exit
fi

if [ -z "$PORT_DEVEL" ]; then
	echo "Please provide the port setting the variable PORT_DEVEL"
	exit
fi


## These directories are local to container
DOCKER_SPOOL=/var/spool/eurotherm
DOCKER_SRC=/usr/local/src/eurotherm


container_name="devel"
export MODE=testing

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
	docker stop "$container_name" >/dev/null 2>&1
	docker rm "$container_name" >/dev/null 2>&1
fi

docker run -d -e MODE=$MODE --name $container_name -p $PORT_DEVEL:80 \
		-v $SOURCES:$DOCKER_SRC \
		-v $ARCHIVE:$DOCKER_SPOOL raffauser/leonardoplanner:devel

