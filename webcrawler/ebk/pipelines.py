# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# as noted in the items.py file in this project only dataclasses are used,
# so we dont use the item adapter and instead use the dataclass syntax consistetly
# from itemadapter import ItemAdapter
from .items import DummyCategory, DummyArticle
import logging


class DummyPipeline:
    def process_item(self, item, spider):
        if isinstance(item, DummyCategory):
            spider.set_attr_from_pipeline(f"category {item.i} {item.j}")
        elif isinstance(item, DummyArticle):
            spider.set_attr_from_pipeline(f"article {item.i}")

        return item
