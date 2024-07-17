#!/bin/sh
export PYTHONPATH=/usr/local/src/eurotherm/src/
export PYTHONPATH=$PYTHONPATH:/usr/local/src/eurotherm/

python3 src/leo_main.py $1


