#/bin/bash

docker run --rm -v "$(pwd):/mnt" build make
