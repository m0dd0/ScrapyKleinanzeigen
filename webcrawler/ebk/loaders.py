import re
from datetime import datetime, timedelta

from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Compose


def _integer_from_string(string: str):
    res = re.sub("\D", "", string)
    if res == "":
        return None
    if len(res) > 1:
        res = res.removeprefix("0")
    return int(res)


def _get_article_datetime(self, datestring: str):
    datestring = datestring.lower()

    # in case the article is a topad only empty string are contained in the topright div
    # also sometimes two strings are in the div from ahich one is only a "\n"
    # in this case abort further parsing by returning None
    if datestring.strip() == "":
        return None

    if re.match("gestern|heute.*", datestring):
        yesterday = datestring.startswith("gestern")
        hour, minute = divmod(self._integer_from_string(datestring), 100)

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
        raise NotImplementedError()


class CategoryLoader(ItemLoader):
    timestamp_out = TakeFirst()
    name_out = Compose(lambda v: v[0], str.strip)
    n_articles_out = Compose(lambda v: v[0], _integer_from_string)
    parent_out = TakeFirst()


class ArticleLoader(ItemLoader):
    name = TakeFirst()
    price = Compose(
        lambda v: v[0],
        str.lower,
        lambda v: {True: "0", False: v}["zu verschenken" in v],
        _integer_from_string,
    )
    negotiable = Compose(lambda v: v[0], str.lower, lambda v: "vb" in v)
    postal_code = Compose(lambda v: re.sub("\D", "", v[-1]))
    timestamp = Compose(lambda v: v[-1], _get_article_datetime)
    description = Compose(lambda v: v[0], lambda v: v.removesuffix("..."))
    sendable = Compose(
        lambda v: [t.lower() for t in v],
        lambda v: "versand möglich" not in v,
    )
    offer = Compose(lambda v: [t.lower() for t in v], lambda v: "gesuch" not in v)
    tags = MapCompose(
        str.lower,
        lambda v: {True: None, False: v}[v in ("gesuch", "versand möglich")],
    )
    main_category: TakeFirst()
    sub_category: TakeFirst()
    business_ad: TakeFirst()
    image_link: TakeFirst()
    pro_shop_link = Compose(lambda v: {False: None, True: v}[bool(len(v))])
    top_ad = Compose(bool)
    highlight_ad = Compose(bool)
