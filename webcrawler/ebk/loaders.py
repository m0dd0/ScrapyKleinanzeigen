import re

from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst, Compose


def _integer_from_string(string: str):
    res = re.sub("\D", "", string)
    if res == "":
        return None
    if len(res) > 1:
        res = res.removeprefix("0")
    return int(res)


class CategoryLoader(ItemLoader):
    timestamp_out = TakeFirst()
    name_out = Compose(lambda v: v[0], str.strip)
    n_articles_out = Compose(lambda v: v[0], _integer_from_string)
    parent_out = TakeFirst()
