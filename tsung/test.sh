#!/bin/sh

set -e

for all in $(find "$(dirname $(readlink -f $0))/tests" -type f -name 'test_*sh'); do 
	echo "INFO: run test $all"
	sh $all
done
