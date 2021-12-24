# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EbkArticle(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    negotiable = scrapy.Field()
    postal_code = scrapy.Field()
    timestamp = scrapy.Field()
    description = scrapy.Field()
    dispatchable = scrapy.Field()
    offer = scrapy.Field()
    tags = scrapy.Field()
    category = scrapy.Field()
    sub_category = scrapy.Field()
    commercial_offer = scrapy.Field()
    image = scrapy.Field()

class Category(scrapy.Item):
    timestamp = scrapy.Field()
    name = scrapy.Field()
    n_childs = scrapy.Field()
    n_articles = scrapy.Field()
    parent = scrapy.Field()
    url_name = scrapy.Field()
    code = scrapy.Field()