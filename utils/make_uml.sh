#!/bin/bash

temp="classes.puml"

echo "@startuml" > $temp

classes=$(grep ^class <(cat src/*.py) | tr ':()' ' ' | awk '{print $2}')

for class in $classes;
do
	awk '
	/^class/ {gsub(/[():]/, "", $2); c=$2}
		/'$class'\(/ {print c, " *-- '$class'"} 
		/\t*self.*'$class'/ {print c, " *-- '$class'"} 
	' <(cat src/*.py)
done | sort | uniq >> $temp

echo "@enduml" >> $temp
cat $temp

plantuml $temp 

echo "UML diagram generated in $(basename $temp .puml).png"

