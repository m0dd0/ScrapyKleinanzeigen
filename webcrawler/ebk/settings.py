# Scrapy settings for ebk project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from scrapy.logformatter import LogFormatter
from scrapy.settings.default_settings import CONCURRENT_ITEMS
from scrapy.utils.log import configure_logging


BOT_NAME = "ebk"

SPIDER_MODULES = ["ebk.spiders"]
NEWSPIDER_MODULE = "ebk.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'ebk.middlewares.EbkSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "ebk.pipelines.DatabaseWriterPipeline": 300,
}
# even if it seems that the crawler always waits for every until an item is processed
# until the next item is requested to be yield we add this low limit
# this ensures that in case of thhe detection of a duplicated scraped article
# we have enough time to set the according flag to inform the spider that
# no next article page requests shall be yielded
CONCURRENT_ITEMS = 10

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

LOGSTATS_INTERVAL = 10

# these settings only affect the output to stdout, we keep them enabled so we can
# use commadn line flags etc (This woulndt be possible if we set a streamlogger manually)
LOG_ENABLED = True  # keep this enabled to still have the "default" stdout ouput
LOG_LEVEL = logging.INFO
# this is the actual formatting string which is used in the logging.Formatter of scrapys logging handler
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
# this only defines how the different messages type (crawl, item found, ...) look like and which level they have
# LOG_FORMATTER = 'scrapy.logformatter.LogFormatter'


# for other handlers than the one to stdout simply add the handlers to the root
# logger. It seems like all scrapy loggers use the handlers from the root logger.
# The settings here do not affect the general logging settings at all.
# configure_logging(install_root_handler=False)
root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)
rotating_handler = logging.handlers.TimedRotatingFileHandler(
    Path(__file__).parent / "log" / "DummyScraperLog",
    when="midnight",
    backupCount=30,
)
rotating_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT))  # use the same log_format
root_logger.addHandler(rotating_handler)
