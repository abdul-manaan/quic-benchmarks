#/bin/bash

/sbin/tc qdisc del dev lo root
/sbin/tc qdisc del dev lo ingress
/sbin/tc qdisc del dev ifb6756 root
/usr/bin/ip link set dev ifb6756 down
/usr/bin/ip link delete ifb6756 type ifb

/sbin/tc qdisc add dev lo root handle 1a64: htb default 1
/sbin/tc class add dev lo parent 1a64: classid 1a64:1 htb rate 10000000.0kbit
/sbin/tc class add dev lo parent 1a64: classid 1a64:104 htb rate 100000.0Kbit ceil 100000.0Kbit burst 12500.0KB cburst 12500.0KB
/sbin/tc qdisc add dev lo parent 1a64:104 handle 2054: netem
/sbin/tc filter add dev lo protocol ip parent 1a64: prio 5 u32 match ip dst 0.0.0.0/0 match ip src 0.0.0.0/0 flowid 1a64:104

modprobe ifb
/usr/bin/ip link add ifb6756 type ifb
/usr/bin/ip link set dev ifb6756 up
/sbin/tc qdisc add dev lo ingress
/sbin/tc filter add dev lo parent ffff: protocol ip u32 match u32 0 0 flowid 1a64: action mirred egress redirect dev ifb6756
/sbin/tc qdisc add dev ifb6756 root handle 1a64: htb default 1
/sbin/tc class add dev ifb6756 parent 1a64: classid 1a64:1 htb rate 32000000.0kbit
/sbin/tc class add dev ifb6756 parent 1a64: classid 1a64:104 htb rate 100000.0Kbit ceil 100000.0Kbit burst 12500.0KB cburst 12500.0KB
/sbin/tc qdisc add dev ifb6756 parent 1a64:104 handle 2054: netem
/sbin/tc filter add dev ifb6756 protocol ip parent 1a64: prio 5 u32 match ip dst 0.0.0.0/0 match ip src 0.0.0.0/0 flowid 1a64:104