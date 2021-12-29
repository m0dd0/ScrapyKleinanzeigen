import logging
import scrapy
from scrapy.utils.project import get_project_settings
import sqlalchemy as sa
import sqlalchemy.orm as orm
import pandas as pd
from datetime import datetime

from .items import Category, CategoryORM, EbkArticle, EbkArticleORM, Base

# as noted in the items.py file in this project only dataclasses are used,
# so we dont use the item adapter and instead use the dataclass syntax consistetly
# from itemadapter import ItemAdapter


class DatabaseWriterPipe:
    def __init__(self):
        pass

    def open_spider(self, spider):
        database_url = get_project_settings().get("DATABASE_URL")
        engine = sa.create_engine(database_url)
        Base.metadata.create_all(engine)
        self.session = orm.sessionmaker(bind=engine)()
        self.commit_delta = get_project_settings().get("DATABASE_COMMIT_DELTA")

    # def _is_duplicate(self, article):
    #     return self.session.query(
    #         sa.sql.exists().where(
    #             sa.and_(
    #                 EbkArticleORM.name == article.name,
    #                 EbkArticleORM.timestamp == article.timestamp,
    #                 EbkArticleORM.price == article.price,
    #                 EbkArticleORM.sub_category == article.sub_category,
    #                 EbkArticleORM.postal_code == article.postal_code,
    #                 EbkArticleORM.top_ad == False,
    #             )
    #         )
    #     ).scalar()

    def process_item(self, item, spider):
        if isinstance(item, EbkArticle):
            article_orm = EbkArticleORM.from_item(item)
            # filtering take a lot of time (nearly doubles the needed time for scraping)
            # therfore we do not filter while scraping and instead filter the database
            # also duplicate filtering does not work suffiently
            # afterwads
            # if False: self._is_duplicate(article_orm):
            #     spider.scraping_stats.increment_counter(
            #         article_orm.sub_category, article_orm.is_business_ad, "duplicates"
            #     )
            #     raise scrapy.exceptions.DropItem("Dropped duplicated article.")
            self.session.add(article_orm)

        elif isinstance(item, Category):
            self.session.add(CategoryORM.from_item(item))

        if len(self.session.new) >= self.commit_delta:
            self.session.commit()

        return item

    def close_spider(self, spider):
        self.session.commit()
