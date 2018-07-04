#!/bin/sh
#
# slave netstat monitor
#```
#noff
#non --iface eth0
#non --iface enp4s0f1
#```
#
# slave benchmark
#```
#metalib/bin/node_benchmark.sh
#```
# perftest
#```
#sh tg/tests/perftest.sh 1>>tg_perftest.log 2>&1; sh tg/tests/perftest.sh 1>>tg_perftest.log 2>&1; sh tg/tests/perftest.sh 1>>tg_perftest.log 2>&1;
#```


export IP4TARGET=""
export IP6TARGET=""


metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 UdpRandomPayload --ip4_destination_address ${IP4TARGET} --length 0"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 UdpRandomPayload --ip4_destination_address ${IP4TARGET} --length 100"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 UdpRandomPayload --ip4_source_address drnd --ip4_destination_address ${IP4TARGET} --length 1300"
sleep 60


metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 TcpHeader --ip4_destination_address ${IP4TARGET}"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 TcpHeader --ip4_destination_address ${IP4TARGET} --tcp_source_port drnd"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 TcpHeader --ip4_source_address drnd --ip4_destination_address ${IP4TARGET} --tcp_source_port drnd"
sleep 60


metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 IcmpEcho --ip4_destination_address ${IP4TARGET}"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 IcmpEcho --ip4_destination_address ${IP4TARGET} --icmpecho_data $(python -c 'print "A"*2')"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 IcmpEcho --ip4_source_address drnd --ip4_destination_address ${IP4TARGET} --icmpecho_data $(python -c 'print "A"*100')"





metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Udp6RandomPayload --ip6_destination_address ${IP6TARGET} --length 0"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Udp6RandomPayload --ip6_destination_address ${IP6TARGET} --length 100"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Udp6RandomPayload --ip6_source_address drnd --ip6_destination_address ${IP6TARGET} --length 1300"
sleep 60


metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Tcp6Header --ip6_destination_address ${IP6TARGET}"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Tcp6Header --ip6_destination_address ${IP6TARGET} --tcp_source_port drnd"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Tcp6Header --ip6_source_address drnd --ip6_destination_address ${IP6TARGET} --tcp_source_port drnd"
sleep 60


metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Icmp6Echo --ip6_destination_address ${IP6TARGET}"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Icmp6Echo --ip6_destination_address ${IP6TARGET} --icmp6echo_data $(python -c 'print "A"*2')"
sleep 60
metalib/bin/perftest_netstat.py --perftest_time 60 --perftest_cmd "tg/tg2 Icmp6Echo --ip6_destination_address ${IP6TARGET} --icmp6echo_data $(python -c 'print "A"*100')"
sleep 60
