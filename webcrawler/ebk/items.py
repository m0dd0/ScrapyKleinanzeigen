import re

import sqlalchemy as sa
from sqlalchemy import orm

from .parsing import eval_price_string, eval_timestamp_str, integer_from_string


class EbkArticle(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def from_raw(
        cls,
        name,
        price_string,
        postal_code,
        timestamp,
        description,
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
        return cls(
            name=name,
            price=eval_price_string(price_string),
            negotiable="vb" in price_string.lower() if price_string else False,
            postal_code=re.sub("\D", "", postal_code[-1]),
            timestamp=eval_timestamp_str(timestamp),
            description=description[0].removesuffix("..."),
            sendable="versand möglich" not in tags,
            offer="gesuch" not in tags,
            tags=tags,
            main_category=main_category,
            sub_category=sub_category,
            is_business_ad=is_business_ad,
            image_link=f"https://www.ebay-kleinanzeigen.de{image_link}"
            if image_link
            else None,
            pro_shop_link=f"https://www.ebay-kleinanzeigen.de{pro_shop_link}"
            if pro_shop_link
            else None,
            top_ad=False if top_ad is None else True,
            highlight_ad=False if highlight_ad is None else True,
            link=f"https://www.ebay-kleinanzeigen.de{link}",
            crawl_timestamp=crawl_timestamp,
        )


class Category(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def from_raw(cls, timestamp, name, n_articles, parent):
        return cls(
            timestamp=timestamp,
            name=name.strip(),
            n_articles=integer_from_string(n_articles),
            parent=parent,
        )


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
        return cls(**item)


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
        return cls(**item)


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
