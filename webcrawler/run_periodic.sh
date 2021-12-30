#!/bin/bash

while true
do
    scrapy crawl search_spider --loglevel=INFO -O ../data/last_run.json -a max_age=900 -a max_runtime=900 &
    sleep 3600
done
