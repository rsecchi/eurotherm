#!/bin/bash



TESTNAME="
	Abitazioni-000_070 
	Abitazioni-071_105 
	Abitazioni-106_165 
	Abitazioni-166_260 
	Abitazioni-260-end
"

LEO_DIR=$PWD/..
LOCAL_DIR=$PWD


for TYPE in 55 35 30;
do

	for TEST in $TESTNAME;
	do

		export ARCHIVE=/home/raffaello/eurotherm/planimetrie/$TEST
		echo $ARCHIVE

		# Reload the configuration
		docker stop devel
		cd $LEO_DIR/Docker
		./run_devel_image.sh
		cd $LOCAL_DIR
		
		# Run the tests
		docker exec -it devel /usr/bin/python3 \
			/usr/local/src/eurotherm/benchmark/run_tests_${TYPE}.py
		./parse.sh $ARCHIVE

		mv $ARCHIVE/LEO_test.csv ${TEST}-${TYPE}.csv

	done

done

ssconvert *.csv --merge-to=LEO-tests.xls

