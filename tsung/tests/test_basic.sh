#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh

# random uri
URI=$(/bin/dd if=/dev/urandom bs=100 count=1 2>/dev/null | /usr/bin/shasum | /usr/bin/awk '{print $1}')

# run test
run $URI

# test requested URI in webserver log
check_value $URI

cleanup
rreturn 0 "$0"
