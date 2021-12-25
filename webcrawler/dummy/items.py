# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from dataclasses import dataclass

# DESIGN DESCISSION:
# we will use only dataclass as item type
# this allows to use the ite.attribute API and therfore enabled the usage of intellisene
# also it is a standard python datatype
# it also allows for metadata, do there is no disadvantage compared to scrapy.Item


@dataclass
class DummyCategory:
    i: int
    j: int


@dataclass
class DummyArticle:
    i: int
