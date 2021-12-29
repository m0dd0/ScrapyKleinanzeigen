from datetime import datetime
from tabulate import tabulate

import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request

from ..loaders import ArticleLoader, CategoryLoader
from ..items import Category, EbkArticle


class ScrapingStats:
    def __init__(self) -> None:
        self._data = {}

    def add_category(self, name, business):
        assert (name, business) not in self._data.keys()
        self._data[(name, business)] = {
            "pages": 0,
            "articles": 0,
        }

    def increment_counter(self, name, business, counter):
        self._data[(name, business)][counter] += 1

    def get_count(self, name, business, counter):
        return self._data[(name, business)][counter]

    def get_category(self, name, business):
        return self._data[(name, business)]

    def add_abortion_reaseon(self, name, business, reason):
        self._data[(name, business)]["abortion_reason"] = reason

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
        *args,
        **kwargs,
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

        super().__init__(*args, **kwargs)

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
        current_timestamp = int(datetime.now().timestamp())

        self._yielded_subcategory_names = []

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
        return f"Aborted crawling of {sub_category} ({business_type_mapping[is_business_ad]}) due to "

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
            article_loader = ArticleLoader(EbkArticle(), article_)
            article_loader.add_value("main_category", main_category)
            article_loader.add_value("sub_category", sub_category)
            article_loader.add_value("is_business_ad", is_business_ad)
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
            middle_subloader.add_css("link", "h2 a::attr(href)")

            bottom_subloader = article_loader.nested_css(".aditem-main--bottom")
            bottom_subloader.add_css("tags", ".text-module-end.simpletag::text")
            bottom_subloader.add_css("offer", ".text-module-end.simpletag::text")
            bottom_subloader.add_css("sendable", ".text-module-end.simpletag::text")
            bottom_subloader.add_css(
                "pro_shop_link", ".text-module-oneline a::attr(href)"
            )

            article_item = article_loader.load_item()
            self.scraping_stats.increment_counter(
                sub_category, is_business_ad, "articles"
            )
            yield article_item

            if self._check_abortion_article(article_item, sub_category, is_business_ad):
                return

        if self._check_abortion_page(articles_, sub_category, is_business_ad):
            return

        nex_page_url = response.css(".pagination-next::attr(href)").get()
        if nex_page_url is None:
            return

        yield response.follow(
            nex_page_url,
            callback=self.parse_article_page,
            cb_kwargs={
                "main_category": main_category,
                "sub_category": sub_category,
                "is_business_ad": is_business_ad,
            },
        )

    def closed(self, reason):
        self.logger.info(f"\n{self.scraping_stats}")
