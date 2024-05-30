#!/bin/bash

rm polygon-*.png

for i in $(seq 1 1000);
do
	./test_engine  $i
done

convert polygon-*.png output.pdf

