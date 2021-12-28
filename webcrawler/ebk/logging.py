import logging
from scrapy import logformatter


class CustomLogFormatter(logformatter.LogFormatter):
    def crawled(self, request, response, spider):
        res = super().crawled(request, response, spider)
        res["level"] = logging.INFO
        return res
