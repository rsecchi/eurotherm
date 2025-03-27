#!/bin/bash

export ARCHIVE=~/eurotherm/reg_tests2/
export PORT_DEVEL_TESTS=8083

## These directories are local to container
DOCKER_SPOOL=/var/spool/eurotherm
DOCKER_SRC=/usr/local/src/eurotherm


container_name="devel_regtests"
export MODE=testing

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
	docker stop "$container_name" >/dev/null 2>&1
	docker rm "$container_name" >/dev/null 2>&1
fi

docker run -d -e MODE=$MODE --name $container_name -p $PORT_DEVEL_TESTS:80 \
		-v $SOURCES:$DOCKER_SRC \
		-v $ARCHIVE:$DOCKER_SPOOL raffauser/leonardoplanner:devel

