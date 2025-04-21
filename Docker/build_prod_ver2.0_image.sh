#!/bin/bash

# if ! git diff --exit-code; then
# 	echo "Please commit and push changes first"
# 	exit
# fi

docker build --no-cache --network=host -t raffauser/leonardoplanner:ver2 -f Dockerfile.ver2.0 .


#docker login
#docker tag eurotherm:devel raffauser/leonardoplanner:devel
#docker tag eurotherm:prod raffauser/leonardoplanner:prod

#docker push raffauser/leonardoplanner:devel
#docker push raffauser/leonardoplanner:prod

docker push raffauser/leonardoplanner:ver2
