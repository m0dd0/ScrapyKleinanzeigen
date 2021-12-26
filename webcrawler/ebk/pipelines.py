# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# as noted in the items.py file in this project only dataclasses are used,
# so we dont use the item adapter and instead use the dataclass syntax consistetly
# from itemadapter import ItemAdapter
# from .items import Category, DummyCategory, DummyArticle
import logging


class DefaultSetterPipeline:
    def process_item(self, item, spider):
        item.setdefault("field1", "value1")
        item.setdefault("field2", "value2")
        # ...
        return item


# class OrmConverterPipeline:
#     def process_item(self, item_spider):
#         if isinstance(item, Category):
#             return OsmCategory.from_scapy_item(item)
#         elif isinstance(item, Article):
#             return OsmArticle.from_scrapy_imte(item)
#         else:
#             raise ValueError("There is no orm mapper")

# class DuplicateFilterPipeline:
#     def on_spider(self, spider):
#         pass

#     def process_item(self, item, spider):
#         if isinstance(item, Category):
#             pass
#             # spider.set_attr_from_pipeline(f"category {item.i} {item.j}")
#         elif isinstance(item, Article):
#             pass
#             # spider.set_attr_from_pipeline(f"article {item.i}")

#         return item


class DumyOrm:
    def __init__(self) -> None:
        pass


class DatabaseWriterPipeline:
    def process_item(self, item, spider):
        logging.getLogger(__name__).debug("database pipelein")
        return DumyOrm()
