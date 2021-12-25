from time import time
import scrapy
from scrapy.http import HtmlResponse
from ..items import Category, EbkArticle
import re
from datetime import datetime, timedelta


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def _integer_from_string(self, string: str):
        res = re.sub("\D", "", string)
        if res == "":
            return None
        if len(res) > 1:
            res = res.removeprefix("0")
        return int(res)

    def _get_article_datetime(self, datestring: str, current_datetime: datetime):
        datestring = datestring.lower()

        yesterday = datestring.startswith("gestern")
        hour, minute = divmod(self._integer_from_string(datestring), 100)

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

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        timestamp = int(datetime.now().timestamp())

        for main_cat_li_ in response.css(".contentbox .l-container-row"):
            main_cat_h2_ = main_cat_li_.css(".treelist-headline")[0]

            main_cat_name = main_cat_h2_.css("a::text").get().strip()
            main_cat_articlecount = self._integer_from_string(
                main_cat_h2_.css(".text-light::text").get()
            )
            yield Category(
                timestamp=timestamp,
                name=main_cat_name,
                n_articles=main_cat_articlecount,
                parent=None,
            )

            for sub_cat_li_ in main_cat_li_.css("ul li"):
                sub_cat_a_ = sub_cat_li_.css("a")[0]

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
                yield article_request

    def parse_article_page(self, response: HtmlResponse):
        current_datetime = datetime.now()

        for article_ in response.css(".aditem"):
            # do not use seöf._integer_from_String since it might contain leading 0
            postal_code = re.sub(
                "\D", "", article_.css(".aditem-main--top--left::text").getall()[-1]
            )
            article_main_div_ = article_.css(".aditem-main--middle")
            name = article_main_div_.css("h2 a::text").get()
            description = (
                article_main_div_.css(".aditem-main--middle--description::text")
                .get()
                .removesuffix("...")
            )
            price_str = (
                article_main_div_.css(".aditem-main--middle--price").get().lower()
            )
            price = self._integer_from_string(price_str)
            negotiable = "vb" in price_str
            if "zu verschenken" in price_str:
                price = 0

            article_main_topright_div = article_main_div_.css(
                ".aditem-main--top--right"
            )
            toparticle = bool(
                article_main_topright_div.css(".icon-feature-topad").get()
            )
            highlight_article = bool(
                article_main_topright_div.css(".icon-feature-highlight").get()
            )

            timestamp = None
            if not toparticle and not highlight_article:
                timestamp = int(
                    self._get_article_datetime(
                        article_main_topright_div.css(".icon::text").get(),
                        current_datetime,
                    ).timestamp()
                )

            tags = article_.css(
                ".aditem-main--bottom.text-module-end.simpletag::text"
            ).getall()
            tags = [t.lower() for t in tags]

            offer = "gesuch" not in tags
            if not offer:
                tags.remove("gesuch")
            dispatchable = "versand möglich" in tags
            if dispatchable:
                tags.remove("versand möglich")

            yield EbkArticle(
                name=name,
                price=price,
                negotiable=negotiable,
                postal_code=postal_code,
                timestamp=timestamp,
                description=description,
                dispatchable=dispatchable,
                offer=offer,
                tags=tags,
                main_category=response.meta["main_category"],
                sub_category=response.meta["sub_category"],
            )

    sub_category = scrapy.Field()
    commercial_offer = scrapy.Field()
    image = scrapy.Field()
