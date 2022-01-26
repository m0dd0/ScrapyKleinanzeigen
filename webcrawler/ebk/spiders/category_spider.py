import math
from datetime import datetime
from itertools import product

import scrapy
from scrapy.http import HtmlResponse
import pandas as pd

from ..items import EbkArticle, CrawlStatsORM


class CategorySpider(scrapy.Spider):
    name = "category_spider"

    def __init__(
        self,
        category_url,
        max_pages=50,
        max_articles=None,
        max_age=None,
        min_timestamp=None,
        max_runtime=None,
        seperate_business_ads=True,
        seperate_regions=False,
        *args,
    ):
        self.start_timestamp = int(datetime.now().timestamp())
        self.category_url = category_url
        self.category = self.category_url.split("/")[-2].removeprefix("s-")
        self.category_code = self.category_url.split("/")[-1]

        self.max_pages = math.inf if max_pages is None else int(max_pages)
        self.logger.info(f"max_pages: {self.max_pages}")

        self.max_articles = math.inf if max_articles is None else int(max_articles)
        self.logger.info(f"max_articles: {self.max_articles}")

        min_timestamp = 0 if min_timestamp is None else int(min_timestamp)
        min_timestamp_age = 0 if max_age is None else self.start_timestamp - max_age
        self.min_timestamp = max(min_timestamp, min_timestamp_age)
        self.logger.info(f"min_timestamp: {datetime.fromtimestamp(self.min_timestamp)}")

        self.max_runtime = math.inf if max_runtime is None else int(max_runtime)
        self.logger.info(f"max_runtime: {self.max_runtime}")

        self.seperate_business_ads = seperate_business_ads in (
            True,
            "y",
            "yes",
            "true",
            "True",
            "1",
        )
        self.logger.info(f"seperate_business_ads: {self.seperate_business_ads}")

        self.seperate_regions = seperate_regions
        self.logger.info(f"seperate_regions: {self.seperate_regions}")

        self.n_articles = 0
        self.n_pages = 0
        self.abortion_reasons = set()

        super().__init__(*args)

    # @classmethod
    # def from_name(cls, category: str):
    #     return {"autos": "https://www.ebay-kleinanzeigen.de/s-autos/c216"}[
    #         category.lower()
    #     ]

    def start_requests(self):
        is_business_url_parts = ["anbieter:privat", "anbieter:gewerblich"]
        regions_url_parts = [
            "baden-wuerttemberg",
            "bayern",
            "berlin",
            "brandenburg",
            "bremen",
            "hamburg",
            "hessen",
            "mecklenburg-vorpommern",
            "niedersachsen",
            "nordrhein-westfalen",
            "rheinland-pfalz",
            "saarland",
            "sachsen",
            "sachsen-anhalt",
            "schleswig-holstein",
            "thueringen",
        ]

        if not self.seperate_business_ads and not self.seperate_regions:
            injects = [[]]
        elif self.seperate_business_ads and not self.seperate_region:
            injects = [[inj] for inj in is_business_url_parts]
        elif self.seperate_regions and not self.seperate_business_ads:
            injects = [[inj] for inj in regions_url_parts]
        elif self.seperate_business_ads and self.sperate_Regions:
            injects = product(regions_url_parts, is_business_url_parts)
            injects = [list(t) for t in injects]

        url_parts = self.category_url.split("/")
        urls = ["/".join(url_parts[:-1] + inj + url_parts[-1]) for inj in injects]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_article_page)

    def _handle_abortion(self, reasons, url):
        self.logger.info(f"Aborted crawling of {url} due to {reasons}.")
        self.abortion_reasons.update(reasons)

    def _check_abortion(self, article_item=None):
        abortion_reasons = []

        if self.n_pages >= self.max_pages:
            abortion_reasons.append("pages")

        if int(datetime.now().timestamp()) - self.start_timestamp > self.max_runtime:
            abortion_reasons.append("runtime")

        if (
            article_item
            and article_item["timestamp"]
            and article_item["timestamp"] < self.min_timestamp
        ):
            abortion_reasons.append("timestamp")

        if self.n_articles >= self.max_articles:
            abortion_reasons.append("articles")

        return abortion_reasons

    def parse_article_page(self, response: HtmlResponse, is_business_ad: bool):
        self.n_pages += 1

        articles_ = response.css(".aditem")
        if len(articles_) == 0:
            self._handle_abortion({"blocked"}, response.url)
            return

        for article_ in articles_:
            article_topleft_ = article_.css(".aditem-main--top--left")[0]
            article_topright_ = article_.css(".aditem-main--top--right")[0]
            article_middle_ = article_.css(".aditem-main--middle")[0]
            article_bottom_ = article_.css(".aditem-main--bottom")[0]

            article_item = EbkArticle.from_raw(
                main_category=None,
                sub_category=self.category,
                is_business_ad=is_business_ad,
                crawl_timestamp=self.start_timestamp,
                image_link=article_.css(".imagebox::attr(data-imgsrc)").get(),
                postal_code=article_topleft_.css("::text")[-1].get(),
                top_ad=article_topright_.css(".icon-feature-topad").get(),
                highlight_ad=article_topright_.css(".icon-feature-highlight").get(),
                timestamp=article_topright_.css("::text")[-1].get(),
                name=article_middle_.css("h2 a::text").get(),
                description=article_middle_.css(
                    ".aditem-main--middle--description::text"
                ).get(),
                price_string=article_middle_.css(
                    ".aditem-main--middle--price::text"
                ).get(),
                link=article_middle_.css("h2 a::attr(href)").get(),
                tags=article_bottom_.css(".text-module-end .simpletag::text").getall(),
                pro_shop_link=article_bottom_.css(
                    ".text-module-oneline a::attr(href)"
                ).get(),
            )

            self.n_articles += 1
            yield article_item

            abortion_reasons = self._check_abortion(article_item=article_item)
            if abortion_reasons:
                self._handle_abortion(abortion_reasons, response.url)
                return

        next_page_url = response.css(".pagination-next::attr(href)").get()
        if next_page_url is None:
            self._handle_abortion({"no_pages"}, response.url)
            return

        yield response.follow(
            next_page_url,
            callback=self.parse_article_page,
            cb_kwargs={"is_business_ad": is_business_ad},
        )

    def closed(self, reason):
        stats_orm = CrawlStatsORM(
            start_timestamp=self.start_timestamp,
            category=self.category,
            # category_code=self.category_code,
            duration=int(datetime.now().timestamp()) - self.start_timestamp,
            n_pages=self.n_pages,
            n_articles=self.n_articles,
            abortion_reasons=list(self.abortion_reasons),
            max_pages=self.max_pages,
            max_articles=self.max_articles,
            min_timestamp=self.min_timestamp,
            max_runtime=self.max_runtime,
            seperate_business_ads=self.seperate_business_ads,
            seperate_region=self.seperate_regions,
        )
        self.session.add(stats_orm)
        self.session.commit()

        self.logger.info(f"\n{stats_orm}")
