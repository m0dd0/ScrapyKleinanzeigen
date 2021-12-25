# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DummyCategory(scrapy.Item):
    i = scrapy.Field()
    j = scrapy.Field()


class DummyArticle(scrapy.Item):
    i = scrapy.Field()
