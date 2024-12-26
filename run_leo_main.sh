#!/bin/sh
export PYTHONPATH=/usr/local/src/eurotherm/src/
export PYTHONPATH=$PYTHONPATH:/usr/local/src/eurotherm/
export PYTHONPATH=$PYTHONPATH:/usr/local/src/eurotherm/www/cgi-bin
export PYTHONPATH=$PYTHONPATH:/usr/local/src/eurotherm/engine



python3 /usr/local/src/eurotherm/src/leo_main.py "$1"


