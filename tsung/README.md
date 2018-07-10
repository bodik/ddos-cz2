# pytsung -- tsung python frontend

## Requirements

* `python-pyroute2`
* `python-numpy`
* `python3-numpy` (optional for 'perftest\_netstat.py')


## Run

`pytsung --help`


### Tsung node initialization

* build  
 `bin/build.sh`
 
* add all cluster members to /etc/hosts (same on each tsung node)
* ```
 10.10.10.11 tsung1 ts1 
 10.10.10.12 tsung2 ts2  
 10.10.10.13 tsung3 ts3
 ```
 
* ssh trust to itself (optional to all cluster members)  
 *use_controller_vm = 0 -> tsung makes ssh to itself*  
 `cat ~/.ssh/id\_rsa.pub >> ~/.ssh/authorized\_keys`
 `ssh-keyscan -H localhost >> ~/.ssh/known\_hosts`  
 `ssh-keyscan -H tsung2 >> ~/.ssh/known\_hosts` (optional)  
 `ssh-keyscan -H tsung3 >> ~/.ssh/known\_hosts` (optional)

* perform selftest  
 `sh test.sh`
 
* add target to /etc/hosts  
  *tsung perform dns resolution per http request*
  `10.10.10.100  target.example.com tg`

* increase number of open files in OS (/etc/security/limits.conf)  
`root             -       nofile          1000000`
 
### Perfomance test vs nginx
* add tsung's ssh public key to target's authorizations_keys

* add target to tsung's known_hosts
 `ssh-keyscan -H target.example.com >> ~/.ssh/known\_hosts`

* performance test  
 `./test-performance.py --help`
 
* performance test with *metalib/perftest_netstat.py* component
 `./test-performance-wrapper.sh -t target.example.com -p 44444 -s 44445 -i eth0`  
 `ls -alh results`
 
#### Nginx testing configuration
* OS tuning  
```
sysctl -w net.core.somaxconn=65535
```

* nginx.conf   

```
# The optimal value depends on many factors including    
# (but not limited to) the number of CPU 
worker_processes  32;

worker_rlimit_nofile 100000;

events {
    worker_connections  5000;
}

http {
    # copies data between one FD and other from within the kernel
    # faster then read() + write()
    sendfile on;

    # allow the server to close connection on non responding client, this will free up memory
    reset_timedout_connection on;

    # request timed out -- default 60
    client_body_timeout 10;

    # if client stop responding, free up memory -- default 60
    send_timeout 5;

    # server will close connection after this time -- default 75
    keepalive_timeout 15;

    # number of requests client can make over keep-alive -- for testing environment
    keepalive_requests 100000;

    tcp_nodelay on;
    
server {
    listen       44444 backlog=65535;
    listen       44445 ssl backlog=65535;
    server_name  localhost;

    ssl_certificate      /etc/apache2/ssl/default.crt;
    ssl_certificate_key  /etc/apache2/ssl/default.key;

       location / {
        root   /usr/local/nginx/html;
        index  index.html index.htm;
    }
   }

}
```

