from datetime import datetime
import csv
from os import abort
from pathlib import Path

from tabulate import tabulate
import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy.utils.project import get_project_settings
import sqlalchemy as sa
from sqlalchemy import orm

from ..loaders import ArticleLoader, CategoryLoader
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

    def as_list_of_dicts(self, additional_columns=None):
        if additional_columns is None:
            additional_columns = {}
        rows = [
            additional_columns | {"sub_category": c, "is_business_ad": b} | d
            for (c, b), d in self._data.items()
        ]
        return rows

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
        *args,
        # **kwargs,
    ):
        if max_pages is not None:
            max_pages = int(max_pages)
        self.max_pages = max_pages
        self.logger.info(f"max_pages: {self.max_pages}")
        if max_articles is not None:
            max_articles = int(max_articles)
        self.max_articles = max_articles
        self.logger.info(f"max_articles: {self.max_articles}")
        if max_age is not None:
            max_age = int(max_age)  # in seconds
        self.max_age = max_age
        self.logger.info(f"max_age: {self.max_age}")
        if categories is not None:
            categories = categories.split(",")
        self.categories = categories
        self.logger.info(f"categories: {self.categories}")
        if max_runtime is not None:
            max_runtime = int(max_runtime)
        self.max_runtime = max_runtime
        self.logger.info(f"max_runtime: {self.max_runtime}")

        self.seperate_business_ads = seperate_business_ads in (
            True,
            "y",
            "yes",
            "true",
            "True",
            "1",
        )

        self.scraping_stats = ScrapingStats()
        self.start_timestamp = int(datetime.now().timestamp())
        self._yielded_subcategory_names = []

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
                sub_cat_item.name in self.categories
                or sub_cat_item.parent in self.categories
            ):
                self.logger.info(f"Skipping category {sub_cat_item.name}.")
                return []

        if self._yielded_subcategory_names.count(sub_cat_item.name) > 1:
            self.logger.info(
                f"Skipping category ({sub_cat_item.parent}/{sub_cat_item.name}) to avoid duplicated scrawling of sub category."
            )
            return []

        cb_kwargs = {
            "main_category": main_cat_item.name,
            "sub_category": sub_cat_item.name,
        }
        if not self.seperate_business_ads:
            self.scraping_stats.add_category(sub_cat_item.name, None)
            return [
                response.follow(
                    sub_cat_link,
                    callback=self.parse_article_page,
                    cb_kwargs=cb_kwargs | {"is_business_ad": None},
                )
            ]
        else:
            self.scraping_stats.add_category(sub_cat_item.name, True)
            self.scraping_stats.add_category(sub_cat_item.name, False)
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
            main_cat_h2_ = main_cat_li_.css(".treelist-headline")
            main_cat_loader = CategoryLoader(Category(), main_cat_h2_)
            main_cat_loader.add_css("name", "a::text")
            main_cat_loader.add_css("n_articles", ".text-light::text")
            main_cat_loader.add_value("timestamp", self.start_timestamp)
            main_cat_loader.add_value("parent", None)
            main_cat_item = main_cat_loader.load_item()
            yield main_cat_item

            for sub_cat_li_ in main_cat_li_.css("ul li"):

                sub_cat_loader = CategoryLoader(Category(), sub_cat_li_)
                sub_cat_loader.add_css("name", "a::text")
                sub_cat_loader.add_css("n_articles", ".text-light")
                sub_cat_loader.add_value("timestamp", self.start_timestamp)
                sub_cat_loader.add_value("parent", main_cat_item.name)

                sub_cat_link = sub_cat_li_.css("a::attr(href)").get()
                sub_cat_item = sub_cat_loader.load_item()

                yield sub_cat_item
                self._yielded_subcategory_names.append(sub_cat_item.name)

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

        if self.max_pages is not None and stats["pages"] >= self.max_pages:
            self.logger.warning(
                f"{abortion_message} maximum number of pages ({self.max_pages})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "pages"
            )
            return True

        if (
            self.max_runtime is not None
            and int(datetime.now().timestamp()) - self.start_timestamp
            > self.max_runtime
        ):
            self.logger.warning(f"{abortion_message} maximum crawling time reached.")
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "runtime"
            )
            return True

        return False

    def _check_abortion_article(self, article_item, sub_category, is_business_ad):
        abortion_message = self._get_abortion_message_base(sub_category, is_business_ad)
        stats = self.scraping_stats.get_category(sub_category, is_business_ad)

        if (
            self.max_age is not None
            and article_item.timestamp  # top_ads no not have a timestamp
            and self.start_timestamp - article_item.timestamp > self.max_age
        ):
            self.logger.info(f"{abortion_message} age of article ({self.max_age}s).")
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "timestamp"
            )
            return True

        if self.max_articles is not None and stats["articles"] >= self.max_articles:
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
            # article_loader = ArticleLoader(EbkArticle(), article_)
            # article_loader.add_value("main_category", main_category)
            # article_loader.add_value("sub_category", sub_category)
            # article_loader.add_value("is_business_ad", is_business_ad)
            # article_loader.add_value("crawl_timestamp", self.start_timestamp)
            article_loader = article_
            topleft_subloader = article_loader.css(".aditem-main--top--left")[0]
            topright_subloader = article_loader.css(".aditem-main--top--right")[0]
            middle_subloader = article_loader.css(".aditem-main--middle")[0]
            bottom_subloader = article_loader.css(".aditem-main--bottom")[0]
            article_item = EbkArticle(
                main_category=main_category,
                sub_category=sub_category,
                is_business_ad=is_business_ad,
                crawl_timestamp=self.start_timestamp,
                image_link=article_loader.css(".aditem-image img::attr(src)").get(),
                postal_code=topleft_subloader.css("::text").get(),
                top_ad=topright_subloader.css(".icon-feature-topad").get(),
                highlight_ad=topright_subloader.css(".icon-feature-highlight").get(),
                timestamp=topright_subloader.css("::text").get(),
                name=middle_subloader.css("h2 a::text").get(),
                description=middle_subloader.css(
                    ".aditem-main--middle--description::text"
                ).get(),
                price=middle_subloader.css(".aditem-main--middle--price::text").get(),
                negotiable=middle_subloader.css(
                    ".aditem-main--middle--price::text"
                ).get(),
                link=middle_subloader.css("h2 a::attr(href)").get(),
                tags=bottom_subloader.css(".text-module-end .simpletag::text").get(),
                offer=bottom_subloader.css(".text-module-end .simpletag::text").get(),
                sendable=bottom_subloader.css(
                    ".text-module-end .simpletag::text"
                ).get(),
                pro_shop_link=bottom_subloader.css(
                    ".text-module-oneline a::attr(href)"
                ).get(),
            )
            # article_item = {}  # article_loader.load_item()
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
        duration = int(datetime.now().timestamp()) - self.start_timestamp
        additional_columns = {
            "start_timestamp": self.start_timestamp,
            "duration": duration,
        }
        rows = self.scraping_stats.as_list_of_dicts(additional_columns)

        total_articles = sum([r["articles"] for r in rows])
        total_pages = sum([r["pages"] for r in rows])

        file_exists = Path(self.crawling_meta_path).exists()
        with open(self.crawling_meta_path, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(
                    [
                        "start_timestamp",
                        "duration",
                        "n_categories",
                        "total_pages",
                        "total_articles",
                        "pages_per_second",
                        "articles_per_second",
                        "max_pages",
                        "max_article",
                        "max_age",
                        "categories",
                        "seperate_business_ads",
                        "max_runtime",
                    ]
                )
            writer.writerow(
                [
                    self.start_timestamp,
                    duration,
                    len(rows),
                    total_pages,
                    total_articles,
                    total_pages / duration,
                    total_articles / duration,
                    self.max_pages,
                    self.max_articles,
                    self.max_age,
                    self.categories,
                    self.seperate_business_ads,
                    self.max_runtime,
                ]
            )

        for r in rows:
            r["n_pages"] = r.pop("pages")
            r["n_articles"] = r.pop("articles")
            self.session.add(CategoryCrawlORM(**r))

        self.session.commit()
        self.logger.info(f"\n{self.scraping_stats}")
