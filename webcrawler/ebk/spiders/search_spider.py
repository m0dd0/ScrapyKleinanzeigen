import re
from datetime import datetime, timedelta

import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join, Compose

from ..loaders import ArticleLoader, CategoryLoader
from ..items import Category  # , CategoryLoader  # , EbkArticle


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def __init__(self, *args, **kwargs):
        self.duplicate_counter = {}
        super().__init__(*args, **kwargs)

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        current_timestamp = int(datetime.now().timestamp())

        for main_cat_li_ in response.css(".contentbox .l-container-row"):
            main_cat_h2_ = main_cat_li_.css(".treelist-headline")
            main_cat_loader = CategoryLoader(Category(), main_cat_h2_)
            main_cat_loader.add_css("name", "a::text")
            main_cat_loader.add_css("n_articles", ".text-light::text")
            main_cat_loader.add_value("timestamp", current_timestamp)
            main_cat_loader.add_value("parent", None)
            main_cat_item = main_cat_loader.load_item()
            yield main_cat_item

            for sub_cat_li_ in main_cat_li_.css("ul li"):
                sub_cat_loader = CategoryLoader(Category(), sub_cat_li_)
                sub_cat_loader.add_css("name", "a::text")
                sub_cat_loader.add_css("n_articles", ".text-light")
                sub_cat_loader.add_value("timestamp", current_timestamp)
                sub_cat_loader.add_value("parent", main_cat_item.name)
                sub_cat_item = sub_cat_loader.load_item()
                yield sub_cat_item

                sub_cat_a_ = sub_cat_li_.css("a")[0].attrib["href"]
                article_url_base = response.urljoin(sub_cat_a_)
                cb_kwargs = {
                    "main_category": main_cat_item.name,
                    "sub_category": sub_cat_item.name,
                }
                yield Request(
                    f"{article_url_base}/anbieter:privat",
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"business_ad": False},
                )
                yield Request(
                    f"{article_url_base}/anbieter:gewerblich",
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"business_ad": True},
                )

    def parse_article_page(
        self, response: HtmlResponse, main_category, sub_category, business_ad
    ):
        for article_ in response.css(".aditem"):
            article_loader = ArticleLoader(Article(), article_)
            article_loader.add_value("main_category", main_category)
            article_loader.add_value("sub_category", sub_category)
            article_loader.add_value("business_ad", business_ad)
            article_loader.add_css("image_link", ".aditem-image img::attr(src)")

            topleft_subloader = article_loader.nested_css(".aditem-main--top--left")
            topleft_subloader.add_css("postal_code", "::text")

            topright_subloader = article_loader.nested_css(".aditem-main--top--right")
            topright_subloader.add_css("top_ad", ".icon-feature-topad")
            topright_subloader.add_css("highlight_ad", ".icon-feature-highlight")
            topright_subloader.add_css("timestamp", "::text")

            middle_subloader = article_loader.nested_css(".aditem-main--middle")
            middle_subloader.add_css("name", "h2 a::text")
            middle_subloader.add_css(
                "description", ".aditem-main--middle--description::text"
            )
            middle_subloader.add_css("price", ".aditem-main--middle--price::text")
            middle_subloader.add_css("negotiable", ".aditem-main--middle--price::text")

            bottom_subloader = article_loader.nested_css(".aditem-main--bottom")
            bottom_subloader.add_css("tags", ".text-module-end.simpletag::text")
            bottom_subloader.add_css("offer", ".text-module-end.simpletag::text")
            bottom_subloader.add_css("sendable", ".text-module-end.simpletag::text")
            bottom_subloader.add_css(
                "pro_shop_link", ".text-module-oneline a::attr(href)"
            )

            yield article_loader.load_item()

        if response.meta["sub_category"] in self.finished_categories:
            return

        # if page

        yield response.follow(
            response.css("#srchrslt-pagination.pagination-next"),
            callback=self.parse_article_page,
        )
