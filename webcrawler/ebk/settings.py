# https://docs.scrapy.org/en/latest/topics/settings.html

import logging
from pathlib import Path

BOT_NAME = "ebk"

SPIDER_MODULES = ["ebk.spiders"]
NEWSPIDER_MODULE = "ebk.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
# USER_AGENT = "scrapy ebk by mo"
# USER_AGENT = "not the Googlebot"
# USER_AGENT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# SPIDER_MIDDLEWARES = {
#    'ebk.middlewares.EbkSpiderMiddleware': 543,
# }

# DOWNLOADER_MIDDLEWARES = {
#     "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
#     "ebk.middlewares.RotatingUserAgentsMiddleware": 500,
# }
# ROTATING_USER_AGENTS = Path(__file__).parent / "useragents.json"
# ROTATING_USER_AGENTS_SHUFFLE = False

# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

ITEM_PIPELINES = {
    "ebk.pipelines.DatabaseWriterPipe": 400,
}

# even if it seems that the crawler always waits for every until an item is processed
# until the next item is requested to be yield we add this low limit
# this ensures that in case of thhe detection of a duplicated scraped article
# we have enough time to set the according flag to inform the spider that
# no next article page requests shall be yielded
CONCURRENT_ITEMS = 10

DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent.parent / 'data' / 'test.db'}"
DATABASE_COMMIT_DELTA = 100

LOGSTATS_INTERVAL = 10

# these settings only affect the output to stdout, we keep them enabled so we can
# use commadn line flags etc (This woulndt be possible if we set a streamlogger manually)
LOG_ENABLED = True  # keep this enabled to still have the "default" stdout ouput
LOG_LEVEL = logging.INFO
# this is the actual formatting string which is used in the logging.Formatter of scrapys logging handler
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
# this only defines how the different messages type (crawl, item found, ...) look like and which level they have
LOG_FORMATTER = "ebk.logging.CustomLogFormatter"

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
