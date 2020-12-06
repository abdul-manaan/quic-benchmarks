#!/bin/bash

BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

NETWORK_CONDITIONS=(
    "loss-0_delay-0_bw-100"
    "loss-0dot1_delay-0_bw-100"
    "loss-1_delay-0_bw-100"
    "loss-1burst_delay-0_bw-100"
    "loss-1_delay-50_bw-100"
    "loss-0_delay-50_bw-100"
    "loss-0_delay-100_bw-100"
    "loss-0_delay-100jitter_bw-100"
    "loss-0_delay-0_bw-10"
    "loss-0dot1_delay-0_bw-10"
    "loss-1_delay-0_bw-10"
    "loss-1burst_delay-0_bw-10"
    "loss-1_delay-50_bw-10"
    "loss-0_delay-50_bw-10"
    "loss-0_delay-100_bw-10"
    "loss-0_delay-100jitter_bw-10"
)

for network in "${NETWORK_CONDITIONS[@]}"; do
    echo "$network"
    sudo $BASEDIR/network/"$network".sh
    $BASEDIR/run_benchmark.sh $network
done

# Analysis
python3 $BASEDIR/analysis/main.py