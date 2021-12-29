import re
from datetime import datetime, timedelta
from typing import List

from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Compose, Identity


def _integer_from_string(string: str):
    res = re.sub("\D", "", string)
    if res == "":
        return None
    if len(res) > 1:
        res = res.removeprefix("0")
    return int(res)


def _get_article_datetime(datestring: str):
    datestring = datestring.lower().strip()

    # in case the article is a topad only empty string are contained in the topright div
    # also sometimes two strings are in the div from ahich one is only a "\n"
    # in this case abort further parsing by returning None
    if datestring == "":
        return None

    if re.match("gestern|heute.*", datestring):
        yesterday = datestring.startswith("gestern")
        hour, minute = divmod(_integer_from_string(datestring), 100)

        current_datetime = datetime.now()
        article_datetime = datetime(
            current_datetime.year,
            current_datetime.month,
            current_datetime.day,
            hour,
            minute,
            0,
            0,
        )
        if yesterday:
            article_datetime = article_datetime - timedelta(days=1)

        return article_datetime

    else:
        return datetime.strptime(datestring, "%d.%m.%Y")


def _save_first(l: List):
    if len(l) == 0:
        return None
    else:
        return l[0]


class CategoryLoader(ItemLoader):
    timestamp_out = TakeFirst()
    name_out = Compose(lambda v: v[0], str.strip)
    n_articles_out = Compose(lambda v: v[0], _integer_from_string)
    parent_out = TakeFirst()


class ArticleLoader(ItemLoader):
    name_out = TakeFirst()
    price_out = Compose(
        _save_first,
        str.lower,
        lambda v: {True: "0", False: v}["zu verschenken" in v],
        _integer_from_string,
    )
    negotiable_out = Compose(_save_first, str.lower, lambda v: "vb" in v)
    postal_code_out = Compose(lambda v: re.sub("\D", "", v[-1]))
    timestamp_out = Compose(
        lambda v: v[-1], _get_article_datetime, lambda v: int(v.timestamp())
    )
    description_out = Compose(lambda v: v[0], lambda v: v.removesuffix("..."))
    sendable_out = Compose(
        lambda v: [t.lower() for t in v],
        lambda v: "versand möglich" not in v,
    )
    offer_out = Compose(lambda v: [t.lower() for t in v], lambda v: "gesuch" not in v)
    tags_out = MapCompose(
        str.lower,
        lambda v: {True: None, False: v}[v in ("gesuch", "versand möglich")],
    )
    main_category_out = TakeFirst()
    sub_category_out = TakeFirst()
    is_business_ad_out = TakeFirst()
    image_link_out = TakeFirst()
    pro_shop_link_out = Compose(
        _save_first, lambda v: f"https://www.ebay-kleinanzeigen.de{v}"
    )
    top_ad_out = Compose(bool)
    highlight_ad_out = Compose(bool)
    link_out = Compose(
        lambda v: v[0], lambda v: f"https://www.ebay-kleinanzeigen.de{v}"
    )
