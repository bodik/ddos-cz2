#!/bin/bash

sysctl -a | grep net.ipv4.tcp_tw_reuse
sysctl -a | grep net.ipv4.tcp_tw_recycle
sysctl -a | grep net.ipv4.ip_local_port_range
sysctl -a | grep fs.file-max

sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_tw_recycle=1
sysctl -w net.ipv4.ip_local_port_range="1024 65000"
#sysctl -w fs.file-max=1000000
sysctl -w fs.nr_open=1000000
#ulimit -n 1000000
sysctl -w net.ipv4.tcp_mem='10000000 10000000 10000000'
sysctl -w net.ipv4.tcp_rmem='1024 4096 16384'
sysctl -w net.ipv4.tcp_wmem='1024 4096 16384'
sysctl -w net.core.rmem_max=16384
sysctl -w net.core.wmem_max=16384

#server side 
#sysctl -w net.core.somaxconn=65535
