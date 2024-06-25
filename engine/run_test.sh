#!/bin/bash

min_range=${1:?usage: $0 <min_range> <max_range>}
max_range=${2:?usage: $0 <min_range> <max_range>}

test() {

	rm polygon-*.png

	for i in $(seq 1 1000);
	do
		./test_engine  $i $1 $2 $min_range $max_range
	done  > ./leonardo_stats/leo_${min_range}-${max_range}_qrt${1}_obs${2}.txt 
	convert polygon-*.png ./leonardo_stats/output_qrt$1_obs$2.pdf

	filename=leonardo_stats/leo_${min_range}-${max_range}_qrt${1}_obs${2}.txt

	res=$(echo 'a=load("'$filename'"); printf("%9.3d ",mean(a))' | octave -W)
	echo qrt=$1 obs=$2 "$res"
}


test 0 0 $min_range $max_range
test 1 0 $min_range $max_range
test 0 1 $min_range $max_range
test 1 1 $min_range $max_range


