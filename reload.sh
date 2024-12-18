#!/bin/bash

for TYPE in 55 35 30;
do

	TESTNAME="
		Abitazioni-000_070 
		Abitazioni-071_105 
		Abitazioni-106_165 
		Abitazioni-166_260 
		Abitazioni-260-end
	"

	for TEST in $TESTNAME;
	do

		DIR=/home/raffaello/eurotherm/planimetrie/$TEST

		# Reload the configuration
		cd Docker
		docker stop devel

		export ARCHIVE=$DIR
		echo $ARCHIVE
		./run_devel_image.sh

		docker exec -it devel /usr/bin/python3 \
			/usr/local/src/eurotherm/run_tests_${TYPE}.py

		cd ..
		./parse.sh $ARCHIVE

		mv $DIR/LEO_test.csv csv_files/${TEST}-${TYPE}.csv

	done

done

ssconvert csv_files/*.csv --merge-to=LEO-tests.xls

