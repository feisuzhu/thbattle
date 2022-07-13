#!/bin/bash

function add-rules {
    echo Add LVS rules

    cat <<EOF | ipvsadm -R
    -A -t $NODE_IP:80 -s rr
    -a -t $NODE_IP:80 -r 100.64.0.1:80 -m -w 1
    -A -t $NODE_IP:443 -s rr
    -a -t $NODE_IP:443 -r 100.64.0.1:443 -m -w 1
    -A -t $NODE_IP:7777 -s rr
    -a -t $NODE_IP:7777 -r 100.64.0.4:7777 -m -w 1
    -A -t $NODE_IP:9999 -s rr
    -a -t $NODE_IP:9999 -r 100.64.0.11:9999 -m -w 1
EOF
}

function clear-rules {
    echo Clear LVS rules
    ipvsadm -C
    exit 0
}


add-rules

trap clear-rules SIGINT SIGTERM SIGQUIT

cat <<EOF > pause.c
#include <unistd.h>
void main() { pause(); }
EOF
gcc pause.c -o pause
./pause &
wait
