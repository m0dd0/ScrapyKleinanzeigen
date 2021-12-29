while 
do
    scrapy crawl search_spider --loglevel=INFO -O ../data/last_run.json -a max_age=900
    sleep 1800
done
