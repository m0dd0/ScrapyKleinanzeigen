from datetime import datetime
from pprint import pformat
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
            "duplicates": 0,
        }

    def increase_count(self, name, business, counter):
        self._data[(name, business)][counter] += 1

    def get_count(self, name, business, counter):
        return self._data[(name, business)][counter]

    def get_category(self, name, business):
        return self._data[(name, business)]

    def category_exists(self, name, business):
        return bool(self._data.get((name, business)))

    def add_abortion_reaseon(self, name, business, reason):
        self._data[(name, business)]["abortion_reason"] = reason

    def __repr__(self):
        return tabulate(
            [
                {"category": f"{k[0]} ({'gewerblich' if k[1] else 'privat'})"} | v
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
        max_pages_per_category=3,
        max_articles_per_category=100,
        max_duplicates_per_category=2,
        max_article_age=60 * 60 * 24,
        categories_to_scrawl=None,
        *args,
        **kwargs,
    ):
        self.max_pages_per_category = int(max_pages_per_category)
        self.max_articles_per_category = int(max_articles_per_category)
        self.max_duplicates_per_category = int(max_duplicates_per_category)
        self.max_article_age = int(max_article_age)  # in seconds
        self.categories_to_scrawl = categories_to_scrawl
        if self.categories_to_scrawl is not None:
            self.categories_to_scrawl = self.categories_to_scrawl.split(",")
        self.scraping_stats = ScrapingStats()

        super().__init__(*args, **kwargs)

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        current_timestamp = int(datetime.now().timestamp())

        sub_categories = {}  # {name:(loader, link)}

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

                # sub category can exist in multiple main categories
                sub_cat_name = sub_cat_loader.get_output_value("name")
                if sub_cat_name in sub_categories:
                    sub_cat_loader, _ = sub_categories[sub_cat_name]
                    sub_cat_loader.add_value("parent", main_cat_item.name)
                else:
                    sub_cat_link = sub_cat_li_.css("a::attr(href)").get()
                    sub_categories[sub_cat_name] = (sub_cat_loader, sub_cat_link)

        for sub_cat_loader, sub_cat_link in sub_categories.values():
            sub_cat_item = sub_cat_loader.load_item()

            self.scraping_stats.add_category(sub_cat_item.name, True)
            self.scraping_stats.add_category(sub_cat_item.name, False)

            yield sub_cat_item

            if self.categories_to_scrawl is not None:
                if sub_cat_item.name not in self.categories_to_scrawl:
                    self.logger.info(f"Skipping category {sub_cat_item.name}.")
                    continue

            article_url_parts = response.urljoin(sub_cat_link).split("/")
            article_url_parts.insert(-1, "anbieter:{gewerblich_privat}")
            article_url_base = "/".join(article_url_parts)
            cb_kwargs = {
                "main_category": main_cat_item.name,
                "sub_category": sub_cat_item.name,
            }
            yield Request(
                article_url_base.format(gewerblich_privat="privat"),
                callback=self.parse_article_page,
                cb_kwargs=cb_kwargs | {"is_business_ad": False},
            )
            yield Request(
                article_url_base.format(gewerblich_privat="gewerblich"),
                callback=self.parse_article_page,
                cb_kwargs=cb_kwargs | {"is_business_ad": True},
            )

    def _check_abortion_page(self, articles, sub_category, is_business_ad):
        abortion_message_base = f"Aborted crawling of {sub_category} ({'gewerblich' if is_business_ad else 'privat'}) due to"
        stats = self.scraping_stats.get_category(sub_category, is_business_ad)

        if stats["pages"] >= self.max_pages_per_category:
            self.logger.warning(
                f"{abortion_message_base} maximum number of pages ({self.max_pages_per_category})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "pages"
            )
            return True

        if len(articles) == 0:
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "blocked"
            )
            self.logger.info(f"{abortion_message_base} blocked website.")
            return True

        return False

    def _check_abortion_article(self, article_item, sub_category, is_business_ad):
        current_timestamp = int(datetime.now().timestamp())
        abortion_message_base = f"Aborted crawling of {sub_category} ({'gewerblich' if is_business_ad else 'privat'}) due to maximum"
        stats = self.scraping_stats.get_category(sub_category, is_business_ad)

        if article_item.timestamp:  # top_ads no not have a timestamp
            if current_timestamp - article_item.timestamp > self.max_article_age:
                self.logger.warning(
                    f"{abortion_message_base} age of article ({self.max_article_age}s)."
                )
                self.scraping_stats.add_abortion_reaseon(
                    sub_category, is_business_ad, "timestamp"
                )
                return True

        if stats["articles"] >= self.max_articles_per_category:
            self.logger.warning(
                f"{abortion_message_base} number of articles ({self.max_articles_per_category})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "articles"
            )
            return True

        if stats["duplicates"] > self.max_duplicates_per_category:
            self.logger.info(
                f"{abortion_message_base} number of duplicates ({self.max_duplicates_per_category})."
            )
            self.scraping_stats.add_abortion_reaseon(
                sub_category, is_business_ad, "duplicates"
            )
            return True

        return False

    def parse_article_page(
        self,
        response: HtmlResponse,
        main_category: str,
        sub_category: str,
        is_business_ad: bool,
    ):
        # TODO adjust loffer so that crawled page has INFO level
        self.scraping_stats.increase_count(sub_category, is_business_ad, "pages")

        articles_ = response.css(".aditem")
        for article_ in articles_:
            article_loader = ArticleLoader(EbkArticle(), article_)
            article_loader.add_value("main_category", main_category)
            article_loader.add_value("sub_category", sub_category)
            article_loader.add_value("business_ad", is_business_ad)
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

            article_item = article_loader.load_item()
            self.scraping_stats.increase_count(sub_category, is_business_ad, "articles")
            yield article_item

            if self._check_abortion_article(article_item, sub_category, is_business_ad):
                return

        if self._check_abortion_page(articles_, sub_category, is_business_ad):
            return

        req = response.follow(
            response.css(".pagination-next::attr(href)").get(),
            callback=self.parse_article_page,
            cb_kwargs={
                "main_category": main_category,
                "sub_category": sub_category,
                "is_business_ad": is_business_ad,
            },
        )
        yield req

    def closed(self, reason):
        self.logger.info(f"\n{self.scraping_stats}")
