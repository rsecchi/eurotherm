#!/bin/bash

docker build --no-cache --network=host -t raffauser/leonardoplanner:prod -f Dockerfile.prod .

#docker login
#docker tag eurotherm:devel raffauser/leonardoplanner:devel
#docker tag eurotherm:prod raffauser/leonardoplanner:prod

#docker push raffauser/leonardoplanner:devel
#docker push raffauser/leonardoplanner:prod

