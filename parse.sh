#!/bin/bash

cd $1

cat LEO_*.dat | grep EURO | sed -e 's/.*EURO\t//g' \
	| sort -n | uniq > prods


for FILE in $(ls LEO_test_*.txt);
do
	echo $FILE
	grep "Total processed rooms" $FILE | awk '{print $5}'
	grep "Total collectors" $FILE | awk '{print $4}'
	grep "Total area" $FILE	 | awk '{print $4}'
	grep "Total active area" $FILE | awk '{print $5}'
	grep "Total passive area" $FILE | awk '{print $5}'
	grep "Normal area" $FILE | awk '{print $4}'
	grep "Normal active area" $FILE | awk '{print $5}'
	grep "Normal passive area" $FILE | awk '{print $5}'
	grep "Hydro area" $FILE | awk '{print $4}'
	grep "Hydro active area" $FILE | awk '{print $5}'
	grep "Hydro passive area" $FILE | awk '{print $5}'
	grep "Total perimeter" $FILE | awk '{print $4}'
	grep "Total lines" $FILE | awk '{print $4}'

	FDAT=$(basename $FILE .txt).dat

	cat prods | while read line; 
	do 
		val=$(grep -B 1 "$line" $FDAT | grep -v EURO | tr ',' '.' )
		echo  $val
	done | sed 's/\r//g'
	echo @

done | tr '\n' '#' > LEO_test.tmp

sed 's/#@#/\n/g' LEO_test.tmp > LEO_test.tmp1

sed 's/@#/\n/g; s/,/_/g; s/#/,/g' LEO_test.tmp1 > LEO_test.tmp2

{ echo -n "Filename","Total processed rooms","Total collectors","Total area","Total active area","Total passive area","Normal area","Normal active area","Normal passive area","Hydro area","Hydro active area","Hydro passive area", "Total perimeter","Total lines"
cat prods | tr -d ',' | paste -sd "," | sed 's/\r//g' 
} > LEO_test.tmp3


cat LEO_test.tmp3 LEO_test.tmp2 > LEO_test.csv

