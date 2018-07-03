#!/bin/sh
#time bash metalib/bin/node_benchmark.sh 1>/tmp/benchmark.log 2>&1; cat /tmp/benchmark.log

BASE=$(dirname $(readlink -f $0))
SYSBENCHLOG="/tmp/node_benchmark_sysbench.$$.log"

echo "== NODE DESCRIPTION"
python3 ${BASE}/node_describe.py

echo "== NODE BENCHMARK"
sh ${BASE}/node_sysbench.sh 1>${SYSBENCHLOG} 2>&1
echo "sysbench logfile: ${SYSBENCHLOG}"
egrep 'Doing|execution time \(avg/stddev\)|Memory operations type:|Operations performed:.*ops/sec|Read.*Written.*Total transferred' ${SYSBENCHLOG}
