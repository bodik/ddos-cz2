#!/bin/sh

PNETSTAT=/opt/ddos-cz2/metalib/bin/perftest_netstat.py
RESULTS_DIR=results

rreturn() { echo "$2"; exit $1; }
usage() { echo "Usage: $0 -t TARGET -p PORT -s PORT_SSL -i IFACE" 1>&2; exit 1; }

while getopts "t:p:s:i:" o; do
	case "${o}" in
        	t) TARGET=${OPTARG} ;;
	        p) PORT=${OPTARG} ;;
		s) PORT_SSL=${OPTARG} ;;
		i) IFACE=${OPTARG} ;;
		*) usage ;;
	esac
done

shift "$(($OPTIND-1))"
test -n "$TARGET" || rreturn 1 "ERROR: missing TARGET"
test -n "$PORT" || rreturn 1 "ERROR: missing PORT"
test -n "$PORT_SSL" || rreturn 1 "ERROR: missing PORT_SSL"
test -n "$IFACE" || rreturn 1 "ERROR: missing IFACE"

mkdir -p ${RESULTS_DIR} || rreturn 1 "ERROR: create directory ${RESULTS_DIR} failed"

# PLAIN
for i in 1 2 3 7 8 9 ; do ${PNETSTAT} --netstat_iface ${IFACE} --perftest_cmd "./test-performance.py ${TARGET} --port ${PORT} --repeat 1 --test $i --time 5m --logfile ${RESULTS_DIR}/perftest-$i.log --debug" --perftest_time 310 > ${RESULTS_DIR}/netstat-$i.log; done

# SSL
for i in 4 5 6 10 11 12; do ${PNETSTAT} --netstat_iface ${IFACE} --perftest_cmd "./test-performance.py ${TARGET} --ssl --port ${PORT_SSL} --repeat 1 --test $i --time 5m --logfile ${RESULTS_DIR}/perftest-$i.log --debug" --perftest_time 310 > ${RESULTS_DIR}/netstat-$i.log; done

