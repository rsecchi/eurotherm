#!/bin/bash

docker run -p 8080:8081 -v $PWD/..:/usr/local/src/eurotherm -v $PWD/../spool:/var/spool/eurotherm eurotherm

