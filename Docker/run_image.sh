#!/bin/bash

PORT=8080
ARCHIVE=/data/archive/


DOCKER_SPOOL=/var/spool/eurotherm
DOCKER_SRC=/usr/local/src/eurotherm


container_name="devel"

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
	docker stop "$container_name" >/dev/null 2>&1
	docker rm "$container_name" >/dev/null 2>&1
fi

docker run -d --name $container_name -p $PORT:8081 -v $PWD/../:$DOCKER_SRC -v $ARCHIVE:$DOCKER_SPOOL eurotherm:devel

#docker run -p $PORT:8081 -v $PWD/../:$DOCKER_SRC eurotherm
