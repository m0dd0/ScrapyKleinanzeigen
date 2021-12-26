import os
from scrapy.cmdline import execute

os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    execute(
        [
            "scrapy",
            "crawl",
            "search_spider_dummy",
        ]
    )
except SystemExit:
    pass
