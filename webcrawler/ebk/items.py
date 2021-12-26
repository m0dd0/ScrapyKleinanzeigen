from dataclasses import dataclass, field
from typing import List

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


@dataclass
class EbkArticle:
    name: str
    price: int
    negotiable: bool
    postal_code: str
    timestamp: int
    description: str
    sendable: str
    offer: bool
    tags: List[str]
    main_category: str
    sub_category: str
    business_ad: bool
    image_link: str
    pro_shop_link: str
    top_ad: bool
    highlight_ad: bool


@dataclass
class Category:
    timestamp: int = field(default=None)
    name: int = field(default=None)
    n_articles: int = field(default=None)
    parent: str = field(default=None)
