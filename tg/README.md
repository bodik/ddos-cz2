# tg2 -- trafgen python frontend

## Requirements

* `python-pyroute2`


## Run

`tg2 --help`


## Notes

Beside typical defense for synflooding `net.ipv4.tcp_syncookies`, applications
are setting a listen backlog (`man 3 listen -- int listen(int sockfd, int
backlog)`) which is also limited by kernel's `net.core.somaxconn`
