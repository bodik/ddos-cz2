# orc -- ORChestration agent

client/server agent system for coordinating distributed network of nodes

* router - wamp router (https://wamp-proto.org/, https://github.com/gammazero/nexus)

* slave - agent listening commands in defined subscribed topic
  * `nodes`
  * `tlist`, `exec`, `tstop`
  * `non`, `noff`
  * `tg`, `tgoff`

* master - agent sending and receiving message to the agents network; supports multiple UI frontends
  * listener - prints all received messages (usefull for logging)
  * commander - simple cmd line tool to send messages
  * framed - npyscreen curses frontend
    * `clear`
    * `quit`
    * any other command is interpreted as command to send to the network


## usage

```
# clone and install
git clone
cd orc
sh bin/build-env.sh

# run router
screen -S orc-router -dm sh ./router

# run slave
. env/bin/activate
screen -S orc-slave -dm python3 ./slave
./master
```
