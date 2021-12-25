from time import time
import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from ..items import Category, EbkArticle, DummyArticle, DummyCategory
import re
from datetime import datetime, timedelta


class SearchSpider(scrapy.Spider):
    name = "search_spider_dummy"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def __init__(self, *args, **kwargs):
        self.finished_categories = []
        super().__init__(*args, **kwargs)

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        for i, main_cat_li_ in enumerate(response.css(".contentbox .l-container-row")):
            print(f"spider main cat: {i}")
            yield DummyCategory(i, -1)

            for j, sub_cat_li_ in enumerate(main_cat_li_.css("ul li")):
                print(f"spider sub cat: {i} {j}")
                yield DummyCategory(i, j)

                print("spider yield article page link")
                # yield response.follow(sub_cat_li_.css("a")[0], self.parse_article_page)

    def parse_article_page(self, response: HtmlResponse):
        for i, article_ in enumerate(response.css(".aditem")):
            print(f"spider article: {i}")
            yield DummyArticle(i)

        # yield response.follow(
        #     response.css("#srchrslt-pagination.pagination-next"),
        #     callback=self.parse_article_page,
        # )
