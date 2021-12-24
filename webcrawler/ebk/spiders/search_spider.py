import scrapy
from scrapy.http import HtmlResponse
from ..items import Category
import re
from datetime import date, datetime


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def _integer_from_string(self, string: str):
        return int(re.sub("\D", "", string))

    def start_requests(self):
        start_url = "http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        timestamp = int(datetime.now().timestamp())
        for main_cat_li_ in response.css(".contentbox .l-container-row"):
            main_cat_h2_ = main_cat_li_.css(".treelist-headline")

            main_cat_name = main_cat_h2_.css("a::text").get().strip()
            main_cat_articlecount = self._integer_from_string(
                main_cat_h2_.css(".textlight::text").get()
            )
            yield Category(
                timestamp=timestamp,
                name=main_cat_name,
                n_articles=main_cat_articlecount,
                parent=None,
            )

            for sub_cat_li_ in main_cat_li_.css("ul li"):
                sub_cat_a_ = sub_cat_li_.css("a")

                sub_cat_name = sub_cat_a_.css("::text").get().strip()
                sub_cat_articlecount = self._integer_from_string(
                    sub_cat_li_.css(".text-light").get()
                )
                yield Category(
                    timestamp=timestamp,
                    name=sub_cat_name,
                    n_articles=sub_cat_articlecount,
                    parent=main_cat_name,
                )

                article_request = response.follow(
                    sub_cat_a_, callback=self.parse_article_page
                )
                article_request.meta["main_category"] = main_cat_name
                article_request.meta["sub_category"] = sub_cat_name
                # yield article_request

    def parse_article_page(self, response: HtmlResponse):
        for article_ in response.css(".aditem"):
            pass
            # postal_code = int()article_.css("aditem-main--top--left::text").getall()[-1]
