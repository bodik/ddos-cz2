#!/bin/sh

apt-get install sysbench

for benchtype in cpu threads mutex memory; do
	sysbench --test=$benchtype run
done

BENCHDIR=/scratch/rsyslog2-cluster-fileio-benchmark.$$
#NOTE: for disk intensive applications BENCHSIZE should be >=50G
BENCHSIZE="1G"
mkdir -p $BENCHDIR
cd $BENCHDIR || exit 1
sysbench --num-threads=8 --test=fileio --file-total-size=${BENCHSIZE} --file-test-mode=rndrw prepare
sysbench --num-threads=8 --test=fileio --file-total-size=${BENCHSIZE} --file-test-mode=rndrw run
sysbench --num-threads=8 --test=fileio --file-total-size=${BENCHSIZE} --file-test-mode=rndrw cleanup
rm -rf $BENCHDIR
