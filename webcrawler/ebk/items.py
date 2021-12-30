from dataclasses import dataclass, field, asdict
from typing import List

import sqlalchemy as sa
from sqlalchemy import orm

# DESIGN DESCISSION:
# we will use only dataclass as item type
# this allows to use the ite.attribute API and therfore enabled the usage of intellisene
# also it is a standard python datatype and it also allows for metadata
# Also it allows to easyly set default value which cant be achieved with scrapy.item
# the downside of not beeing able to use he full feature set of scrapy, includeing easier creation
# of item loaders, customizing feed exports, etc. can be compensetaed easily
# I would say that the extraction logic you can define in scrapy.Item(in/outpu_provessor=Processpor())
# should rather be seperated from the item defintion because its rather part of the
# scraping process (in the spider) than further processing, therfore this downside
# is accepted without being a issue

# TODO speed comparison to scrapy.item (no need for asdict)


@dataclass
class EbkArticle:
    name: str = field(default=None)
    price: int = field(default=None)
    negotiable: bool = field(default=None)
    postal_code: str = field(default=None)
    timestamp: int = field(default=None)
    description: str = field(default=None)
    sendable: str = field(default=None)
    offer: bool = field(default=None)
    tags: List[str] = field(default=None)
    main_category: str = field(default=None)
    sub_category: str = field(default=None)
    is_business_ad: bool = field(default=None)
    image_link: str = field(default=None)
    pro_shop_link: str = field(default=None)
    top_ad: bool = field(default=None)
    highlight_ad: bool = field(default=None)
    link: str = field(default=None)
    crawl_timestamp: int = field(default=None)


@dataclass
class Category:
    timestamp: int = field(default=None)
    name: int = field(default=None)
    n_articles: int = field(default=None)
    parent: str = field(default=None)


### ORM MAPPERS

Base = orm.declarative_base()


class EbkArticleORM(Base):
    __tablename__ = "articles"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    price = sa.Column(sa.Integer)
    negotiable = sa.Column(sa.Boolean)
    postal_code = sa.Column(sa.String)
    timestamp = sa.Column(sa.Integer)
    description = sa.Column(sa.String)
    sendable = sa.Column(sa.Boolean)
    offer = sa.Column(sa.Boolean)
    tags = sa.Column(sa.String)  # TODO maybe use mapping/normalization if needed
    main_category = sa.Column(sa.String)  # TODO relationship
    sub_category = sa.Column(sa.String)  # TODO relationship
    is_business_ad = sa.Column(sa.Boolean)
    image_link = sa.Column(sa.String)
    pro_shop_link = sa.Column(sa.String)
    top_ad = sa.Column(sa.Boolean)
    highlight_ad = sa.Column(sa.Boolean)
    link = sa.Column(sa.String)
    crawl_timestamp = sa.Column(sa.Integer)

    def __init__(
        self,
        name,
        price,
        negotiable,
        postal_code,
        timestamp,
        description,
        sendable,
        offer,
        tags,
        main_category,
        sub_category,
        is_business_ad,
        image_link,
        pro_shop_link,
        top_ad,
        highlight_ad,
        link,
        crawl_timestamp,
    ):
        self.name = name
        self.price = price
        self.negotiable = negotiable
        self.postal_code = postal_code
        self.timestamp = timestamp
        self.description = description
        self.sendable = sendable
        self.offer = offer
        self.tags = str(tags)
        self.main_category = main_category
        self.sub_category = sub_category
        self.is_business_ad = is_business_ad
        self.image_link = image_link
        self.pro_shop_link = pro_shop_link
        self.top_ad = top_ad
        self.highlight_ad = highlight_ad
        self.link = link
        self.crawl_timestamp = crawl_timestamp

    @classmethod
    def from_item(cls, item: EbkArticle):
        return cls(**asdict(item))


class CategoryORM(Base):
    __tablename__ = "categories"

    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(sa.Integer)
    name = sa.Column(sa.Integer)
    n_articles = sa.Column(sa.Integer)
    parent = sa.Column(sa.String)  # TODO relationship

    def __init__(self, timestamp, name, n_articles, parent):
        self.timestamp = timestamp
        self.name = name
        self.n_articles = n_articles
        self.parent = parent

    @classmethod
    def from_item(cls, item):
        return cls(**asdict(item))


class CategoryCrawlORM(Base):
    __tablename__ = "stats"

    id = sa.Column(sa.Integer, primary_key=True)
    start_timestamp = sa.Column(sa.Integer)
    duration = sa.Column(sa.Integer)
    sub_category = sa.Column(sa.String)
    is_business_ad = sa.Column(sa.Boolean)
    n_articles = sa.Column(sa.Integer)
    n_pages = sa.Column(sa.Integer)
    abortion_reason = sa.Column(sa.String)

    def __init__(
        self,
        start_timestamp,
        duration,
        sub_category,
        is_business_ad,
        n_articles,
        n_pages,
        abortion_reason,
    ):
        self.start_timestamp = start_timestamp
        self.duration = duration
        self.sub_category = sub_category
        self.is_business_ad = is_business_ad
        self.n_articles = n_articles
        self.n_pages = n_pages
        self.abortion_reason = abortion_reason
