from datetime import datetime
import csv
from pathlib import Path
import pandas as pd
import math

from tabulate import tabulate
import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy.utils.project import get_project_settings
import sqlalchemy as sa
from sqlalchemy import orm

from ..items import Category, CategoryCrawlORM, EbkArticle, Base


class ScrapingStats:
    def __init__(self) -> None:
        self._data = {}

    def add_category(self, name, business):
        assert (name, business) not in self._data.keys()
        self._data[(name, business)] = {
            "pages": 0,
            "articles": 0,
        }
        # self._set_start(name, business)

    def increment_counter(self, name, business, counter):
        self._data[(name, business)][counter] += 1

    def get_count(self, name, business, counter):
        return self._data[(name, business)][counter]

    def get_category(self, name, business):
        return self._data[(name, business)]

    def add_abortion_reaseon(self, name, business, reason):
        self._data[(name, business)]["abortion_reason"] = reason

    def as_list_of_dicts(self):
        rows = [
            {"sub_category": c, "is_business_ad": b} | d
            for (c, b), d in self._data.items()
        ]
        return rows

    def as_dataframe(self):
        business_type_mapping = {None: "all", True: "gewerblich", False: "privat"}
        df_stats = pd.DataFrame(self.as_list_of_dicts())
        df_stats["category_label"] = df_stats[["sub_category", "is_business_ad"]].agg(
            lambda vs: f"{vs[0]} ({business_type_mapping[vs[1]]})", axis=1
        )
        return df_stats

    # def _set_start(self, name, business):
    #     self._data[(name, business)]["time"] = int(datetime.now().timestamp())

    # def stop_time(self, name, business):
    #     started_timestamp = self._data[(name, business)]["time"]
    #     now_timestamp = int(datetime.now().timestamp())
    #     self._data[(name, business)]["time"] = started_timestamp - now_timestamp

    def __repr__(self):
        business_type_mapping = {None: "all", True: "gewerblich", False: "privat"}
        return tabulate(
            [
                {"category": f"{k[0]} ({business_type_mapping[k[1]]})"} | v
                for k, v in self._data.items()
            ],
            headers="keys",
        )


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def __init__(
        self,
        max_pages=50,
        max_articles=None,
        max_age=None,
        categories=None,
        seperate_business_ads=True,
        max_runtime=None,
        min_timestamp=None,
        *args,
        # **kwargs,
    ):
        self.scraping_stats = ScrapingStats()
        self._yielded_subcategory_names = []
        self.start_timestamp = int(datetime.now().timestamp())

        self.max_pages = math.inf if max_pages is None else int(max_pages)
        self.logger.info(f"max_pages: {self.max_pages}")

        self.max_articles = math.inf if max_articles is None else int(max_articles)
        self.logger.info(f"max_articles: {self.max_articles}")

        min_timestamp = 0 if min_timestamp is None else int(min_timestamp)
        min_timestamp_age = 0 if max_age is None else self.start_timestamp - max_age
        self.min_timestamp = max(min_timestamp, min_timestamp_age)
        self.logger.info(f"min_timestamp: {datetime.fromtimestamp(self.min_timestamp)}")

        self.categories = [] if categories is None else categories.split(",")
        self.logger.info(f"categories: {self.categories}")

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

        database_url = get_project_settings().get("DATABASE_URL")
        engine = sa.create_engine(database_url)
        Base.metadata.create_all(engine)
        self.session = orm.sessionmaker(bind=engine)()
        self.commit_delta = get_project_settings().get("DATABASE_COMMIT_DELTA")
        self.crawling_meta_path = get_project_settings().get("CRAWLING_META_PATH")

        super().__init__(*args)

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def _follow_sub_category(self, response, main_cat_item, sub_cat_item, sub_cat_link):
        if self.categories is not None:
            if not (
                sub_cat_item["name"] in self.categories
                or sub_cat_item["parent"] in self.categories
            ):
                self.logger.info(f"Skipping category {sub_cat_item['name']}.")
                return []

        if self._yielded_subcategory_names.count(sub_cat_item["name"]) > 1:
            self.logger.info(
                f"Skipping category ({sub_cat_item['parent']}/{sub_cat_item['name']}) to avoid duplicated scrawling of sub category."
            )
            return []

        cb_kwargs = {
            "main_category": main_cat_item["name"],
            "sub_category": sub_cat_item["name"],
        }
        if not self.seperate_business_ads:
            self.scraping_stats.add_category(sub_cat_item["name"], None)
            return [
                response.follow(
                    sub_cat_link,
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"is_business_ad": None},
                )
            ]
        else:
            self.scraping_stats.add_category(sub_cat_item["name"], True)
            self.scraping_stats.add_category(sub_cat_item["name"], False)
            article_url_parts = response.urljoin(sub_cat_link).split("/")
            article_url_parts.insert(-1, "anbieter:{gewerblich_privat}")
            article_url_base = "/".join(article_url_parts)
            return [
                Request(
                    article_url_base.format(gewerblich_privat="privat"),
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"is_business_ad": False},
                ),
                Request(
                    article_url_base.format(gewerblich_privat="gewerblich"),
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"is_business_ad": True},
                ),
            ]

    def parse_category_catalog(self, response: HtmlResponse):
        self._yielded_subcategory_names = []

        for main_cat_li_ in response.css(".contentbox .l-container-row"):
            main_cat_h2_ = main_cat_li_.css(".treelist-headline")[0]
            main_cat_item = Category.from_raw(
                name=main_cat_h2_.css("a::text").get(),
                n_articles=main_cat_h2_.css(".text-light::text").get(),
                timestamp=self.start_timestamp,
                parent=None,
            )
            yield main_cat_item

            for sub_cat_li_ in main_cat_li_.css("ul li"):

                sub_cat_item = Category.from_raw(
                    name=sub_cat_li_.css("a::text").get(),
                    n_articles=sub_cat_li_.css(".text-light").get(),
                    timestamp=self.start_timestamp,
                    parent=main_cat_item["name"],
                )

                yield sub_cat_item
                self._yielded_subcategory_names.append(sub_cat_item["name"])

                sub_cat_link = sub_cat_li_.css("a::attr(href)").get()
                for req in self._follow_sub_category(
                    response, main_cat_item, sub_cat_item, sub_cat_link
                ):
                    yield req

    def _get_abortion_message_base(self, sub_category: str, is_business_ad: bool):
        business_type_mapping = {None: "all", True: "gewerblich", False: "privat"}
        return f"Aborted crawling of {sub_category} ({business_type_mapping[is_business_ad]}) due to"

    def _check_abortion_page(self, articles, sub_category, is_business_ad):
        abortion_message = self._get_abortion_message_base(sub_category, is_business_ad)
        stats = self.scraping_stats.get_category(sub_category, is_business_ad)

        if len(articles) == 0:
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "blocked"
            )
            self.logger.warning(f"{abortion_message} blocked website.")
            return True

        if stats["pages"] >= self.max_pages:
            self.logger.warning(
                f"{abortion_message} maximum number of pages ({self.max_pages})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "pages"
            )
            return True

        if int(datetime.now().timestamp()) - self.start_timestamp > self.max_runtime:
            self.logger.warning(f"{abortion_message} maximum crawling time reached.")
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "runtime"
            )
            return True

        return False

    def _check_abortion_article(self, article_item, sub_category, is_business_ad):
        abortion_message = self._get_abortion_message_base(sub_category, is_business_ad)
        stats = self.scraping_stats.get_category(sub_category, is_business_ad)

        if article_item["timestamp"] and article_item["timestamp"] < self.min_timestamp:
            self.logger.info(
                f"{abortion_message} timestamp of article ({datetime.fromtimestamp(self.min_timestamp)}s)."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "timestamp"
            )
            return True

        if stats["articles"] >= self.max_articles:
            self.logger.warning(
                f"{abortion_message} number of articles ({self.max_articles})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "articles"
            )
            return True

        # if stats["duplicates"] > self.max_duplicates_per_category:
        #     self.logger.info(
        #         f"{abortion_message} number of duplicates ({self.max_duplicates_per_category})."
        #     )
        #     self.scraping_stats.add_abortion_reaseon(
        #         sub_category, is_business_ad, "duplicates"
        #     )
        #     return True

        return False

    def parse_article_page(
        self,
        response: HtmlResponse,
        main_category: str,
        sub_category: str,
        is_business_ad: bool,
    ):
        self.scraping_stats.increment_counter(sub_category, is_business_ad, "pages")

        articles_ = response.css(".aditem")
        for article_ in articles_:
            article_topleft_ = article_.css(".aditem-main--top--left")[0]
            article_topright_ = article_.css(".aditem-main--top--right")[0]
            article_middle_ = article_.css(".aditem-main--middle")[0]
            article_bottom_ = article_.css(".aditem-main--bottom")[0]

            article_item = EbkArticle.from_raw(
                main_category=main_category,
                sub_category=sub_category,
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

            self.scraping_stats.increment_counter(
                sub_category, is_business_ad, "articles"
            )
            yield article_item

            if self._check_abortion_article(article_item, sub_category, is_business_ad):
                return

        if self._check_abortion_page(articles_, sub_category, is_business_ad):
            return

        next_page_url = response.css(".pagination-next::attr(href)").get()
        if next_page_url is None:
            return

        yield response.follow(
            next_page_url,
            callback=self.parse_article_page,
            cb_kwargs={
                "main_category": main_category,
                "sub_category": sub_category,
                "is_business_ad": is_business_ad,
            },
        )

    def closed(self, reason):
        df_stats = self.scraping_stats.as_dataframe()
        df_stats["start_timestamp"] = self.start_timestamp
        duration = int(datetime.now().timestamp()) - self.start_timestamp
        df_stats["duration"] = duration

        df_spider = pd.DataFrame(
            {
                "start_timestamp": [self.start_timestamp],
                "duration": [int(datetime.now().timestamp()) - self.start_timestamp],
                "n_categories": [len(df_stats.index)],
                "total_pages": [df_stats["pages"].sum()],
                "total_articles": [df_stats["articles"].sum()],
                "pages_per_second": [df_stats["pages"].sum() / duration],
                "articles_per_second": [df_stats["articles"].sum() / duration],
                "min_articles": [df_stats["articles"].min()],
                "min_articles_category": [
                    df_stats.loc[df_stats["articles"].idxmin()]["category_label"]
                ],
                "max_pages": [df_stats["pages"].max()],
                "max_pages_category": [
                    df_stats.loc[df_stats["pages"].idxmax()]["category_label"]
                ],
                "abortion_reasons": [df_stats["abortion_reason"].unique().tolist()],
                "max_pages": [self.max_pages],
                "max_articles": [self.max_articles],
                "max_age": [self.max_age],
                "categories": [self.categories],
                "seperate_business_ads": [self.seperate_business_ads],
                "max_runtime": [self.max_runtime],
            }
        )

        file_exists = Path(self.crawling_meta_path).exists()
        df_spider.to_csv(
            self.crawling_meta_path, mode="a", header=not file_exists, index=False
        )

        df_stats = df_stats.rename(
            columns={"pages": "n_pages", "articles": "n_articles"}
        )
        df_stats = df_stats.drop(["category_label"], axis=1)
        df_stats.to_sql(
            "stats", self.session.get_bind(), if_exists="append", index=False
        )
        self.session.commit()

        self.logger.info(f"\n{self.scraping_stats}")
