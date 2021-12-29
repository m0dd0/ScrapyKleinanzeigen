while 
do
    scrapy crawl search_spider --loglevel=INFO -O ../data/last_run.json -a max_pages=49 -a max_articles=100 -a max_article_age=900
    sleep 600
done
