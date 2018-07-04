# tg2 -- trafgen python frontend

## Requirements

* `python3`
* `python3-pyroute2`
* `python3-scapy`
* `cpp`


## Run

`tg2 --help`


## Notes

### Theoretical Ethernet Maximum Frame Rate

The maximum frame rate is calculated using the minimum values of the following parameters, as described in the IEEE 802.3ae standard:

| | |
|-|-|
| Preamble			| 8 bytes * 8 = 64 bits |
| Frame length (minimum)i	| 64 bytes * 8 = 512 bits |
| Inter-frame gap (minimum)	| 12 bytes * 8 = 96 bits |

> Maximum Frame Rate = MAC Transmit Bit Rate / (Preamble + Frame Length + Inter-frame Gap)

| | |
|-|-|
| Ethernet Maximum Frame Rate		| Rate [fps] |
| 10 Gigabit Ethernet			| 14 880 952.38 |
| Gigabit Ethernet			| 1 488 095.24 |
| Fast Ethernet (100Mb)			| 148 809.53 |
| Ethernet				| 14 880.95 |

* 10GBASE-R operates at 10.3125 Gb/s line rate
* 10GBASE-W operates at 9.95328 Gb/s line rate


### Syn-flood

Beside typical defense for synflooding `net.ipv4.tcp_syncookies`, applications
are setting a listen backlog (`man 3 listen -- int listen(int sockfd, int
backlog)`) which is also limited by kernel's `net.core.somaxconn`. Applies for
monitoring/testing overloading tcp based applications such as webservers.


### Minimal Ethernet frame size

During perftesting, mind that there might be a difference between TX traffic
size on the sender from RX traffic size on receiver due to ethernet padding in
case of short packets.

```
sender:
23:24:57.941105 IP aa.bbb.ccc.dd.49518 > aa.bbb.ccc.ee.12345: UDP, length 1
	0x0000:  4500 001d 5772 4000 4011 9047 AABB CCDD  E...Wr@.@..GN...
	0x0010:  AABB CCEE c16e 3039 0009 5331 00         N....n09..S1.

receiver:
23:24:57.940936 IP aa.bbb.ccc.dd.49518 > aa.bbb.ccc.ee.12345: UDP, length 1
	0x0000:  4500 001d 5772 4000 4011 9047 AABB CCDD  E...Wr@.@..GN...
	0x0010:  AABB CCEE c16e 3039 0009 bb1d 0000 0000  N....n09........
	0x0020:  0000 0000 0000 0000 0000 0000 0000       ..............
```

by AshwinR Jun 27, 2012 12:53 AM (in response to Bindu)
```
FOR THE 802.3 FRAME CONTAINS

Ethernet Header = 18 Bytes [Dst Mac(6) + Src Mac(6) + Length (2) +CRC(4)] 
Minimum Data Portion = 46 Bytes 
Minimum Ethernet Frame Size = 64 Bytes

Frames must be at least 64 bytes long, not including the preamble, so, if the
data field is shorter than 46 bytes, it must be compensated by the Pad field.
The reason for specifying a minimum length lies with the collision-detect
mechanism. In CSMA/CD a station must never be allowed to believe it has
transmitted a frame successfully if that frame has, in fact, experienced a
collision.

In the worst case it takes twice the maximum propagation delay across the
network before a station can be sure that a transmission has been successful.
If a station sends a really short frame, it may actually finish sending and
release the Ether without realising that a collision has occurred.

Thats why it is/has a minimum of 64 Bytes.
```
