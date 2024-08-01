#!/bin/bash

if [ ! -d "$ARCHIVE" ]; then
	echo "Please provide the archive location by setting the variable ARCHIVE"
	exit
fi

if [ -z "$PORT_PROD" ]; then
	echo "Please provide the port by setting the variable PORT_PROD"
	exit
fi

DOCKER_SPOOL=/var/spool/eurotherm
DOCKER_SRC=/usr/local/src/eurotherm
DOCKER_IMG=raffauser/leonardoplanner:ver2
MODE="testing"

container_name="ver2_prod"

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
	docker stop "$container_name" >/dev/null 2>&1
	docker rm "$container_name" >/dev/null 2>&1
fi

docker run -d -e MODE=$MODE --name $container_name -p $PORT_PROD:80  \
	-v $ARCHIVE:$DOCKER_SPOOL $DOCKER_IMG

