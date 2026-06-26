#!/bin/bash

domains=$1
output=$2

if [[ $# -ne 2 ]]; then
    echo "Usage $0 domains output"
    exit 1
fi

if [ ! -f $domains ]
then
    echo "$domains input file does not exist"
    exit 1
fi

if [ ! -f $output ]
then
    source set_cloudflare_env.sh
    #Header
    python3 cloudflare_api.py cloudflare_csv_header >> $output
    #Parallel call to API with delay to be below limit of 1200 API requests per
    #5 min - 25 domains at a time - exit when 300 jobs have failed but wait for
    #running jobs to complete - trying to avoid gateway timeout with 10s delay
    parallel -X -N 25 --bar --delay 10 --halt soon,fail=10 -a $domains -I @@ "python3 cloudflare_api.py api_request @@ >> $output"
fi