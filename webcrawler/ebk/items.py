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
    business_ad: bool = field(default=None)
    image_link: str = field(default=None)
    pro_shop_link: str = field(default=None)
    top_ad: bool = field(default=None)
    highlight_ad: bool = field(default=None)


@dataclass
class Category:
    timestamp: int = field(default=None)
    name: int = field(default=None)
    n_articles: int = field(default=None)
    parent: str = field(default=None)
