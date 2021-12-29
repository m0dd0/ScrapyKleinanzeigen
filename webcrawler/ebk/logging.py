import logging
from scrapy import logformatter

from .items import EbkArticle


class CustomLogFormatter(logformatter.LogFormatter):
    def crawled(self, request, response, spider):
        res = super().crawled(request, response, spider)
        res["level"] = logging.INFO
        return res

    def dropped(self, item, exception, response, spider):
        res = super().dropped(item, exception, response, spider)
        res["level"] = logging.INFO
        # res["msg"] = "Dropped: %(exception)s" + os.linesep + "%(item)s"
        if isinstance(item, EbkArticle):
            res["msg"] = (
                "Dropped: %(exception)s"
                + f"EbkArticle (category: {item.sub_category}, name: '{item.name}')"
            )
        return res
