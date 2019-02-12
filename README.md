# ddos-cz2 -- network stress testing suite

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND


## multi-interface debian networking setup

* https://blog.ls-al.com/linux-routing-two-interfaces-on-same-subnet/

* /etc/iproute2/rt_tables
```
...
1 rt1
2 rt2
```

* /etc/network/interfaces
```
auto dev1
iface dev1 inet static
	address x1
	netmask 255.255.255.0
	gateway xgw
	post-up ip route add x/24 dev dev1 src x1 table rt1
	post-up ip route add default via xgw dev dev1 table rt1
	post-up ip rule add from x1 table rt1


auto dev2
iface dev2 inet static
	address x2
	netmask 255.255.255.0
	post-up ip route add x/24 dev dev2 src x2 table rt2
	post-up ip route add default via xgw dev dev2 table rt2
	post-up ip rule add from x2 table rt1
```

* /etc/sysctl.d/multiinterface.conf 
```
net.ipv4.conf.all.arp_filter = 1
net.ipv4.conf.default.arp_filter = 1
net.ipv4.conf.all.arp_announce = 2
net.ipv4.conf.default.arp_announce = 2
 
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.dev1.rp_filter = 2
net.ipv4.conf.dev2.rp_filter = 2
```

* tsung's ipcontroll.sh

```
#!/bin/sh

ACTION=$1
IF=dev1
NET=netx

if [ "$ACTION" = "add" ]; then
	# split addresses between generators (1: 20-x, 2: x-250)
        for i in `seq 150 250`; do
                ip addr add $NET.$i/24 dev $IF1 label $IF1:$i
		ip rule add from $NET.$i table rt1
        done
fi

if [ "$ACTION" = "del" ]; then
        for i in `seq 150 250`; do
                ip addr del $NET.$i/24 dev $IF1 label $IF1:$i
		ip rule del from $NET.$i table rt1
        done
fi
```
