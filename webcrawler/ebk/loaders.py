import re
from datetime import datetime, timedelta


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


# class Compose:
#     def __init__(self, *functions) -> None:
#         self.functions = functions

#     def __call__(self, value):
#         for f in self.functions:
#             value = f(value)
#             if value is None:
#                 break
#         return value


class MyItemLoader:
    def __init__(self) -> None:
        pass

    def load_item(self):
        return self._data


class CategoryLoader(MyItemLoader):
    def __init__(self, timestamp, name, n_articles, parent) -> None:
        self._data = {
            "timestamp": timestamp,
            "name": name.strip(),
            "n_articles": _integer_from_string(n_articles),
            "parent": parent,
        }


class ArticleLoader(MyItemLoader):
    def __init__(
        self,
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
        tags = [t.lower() for t in tags]
        self._dict = {
            "name": name,
            "price": 0
            if "zu verschenken" in price_string.lower()
            else _integer_from_string(price_string)
            if price_string
            else None,
            "negotiable": "vb" in price_string.lower() if price_string else False,
            "postal_code": re.sub("\D", "", postal_code[-1]),
            "timestamp": int(_get_article_datetime(timestamp).timestamp()),
            "description": description[0].removesuffix("..."),
            "sendable": "versand möglich" not in tags,
            "offer": "gesuch" not in tags,
            "tags": tags,
            "main_category": main_category,
            "sub_category": sub_category,
            "is_business_ad": is_business_ad,
            "image_link": f"https://www.ebay-kleinanzeigen.de{image_link}"
            if image_link
            else None,
            "pro_shop_link": f"https://www.ebay-kleinanzeigen.de{pro_shop_link}"
            if pro_shop_link
            else None,
            "top_ad": False if top_ad is None else True,
            "highlight_ad": False if highlight_ad is None else True,
            "link": f"https://www.ebay-kleinanzeigen.de{link}",
            "crawl_timestamp": crawl_timestamp,
        }
