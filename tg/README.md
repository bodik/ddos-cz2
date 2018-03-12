# tg2 -- trafgen python frontend

## Requirements

* `python-pyroute2`


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
backlog)`) which is also limited by kernel's `net.core.somaxconn
