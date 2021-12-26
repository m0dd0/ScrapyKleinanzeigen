import scrapy
from scrapy.http import HtmlResponse
from scrapy.utils.response import open_in_browser
from ..items import DummyArticle, DummyCategory


class SearchSpider(scrapy.Spider):
    name = "search_spider_dummy"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    custom_settings = {"USER_AGENT": "some value"}

    def __init__(self, *args, **kwargs):
        self.finished_categories = []
        super().__init__(*args, **kwargs)

    def set_attr_from_pipeline(self, attr):
        self.logger.debug("Set argument from item pipeline")
        pass

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        for i, main_cat_li_ in enumerate(response.css(".contentbox .l-container-row")):
            yield DummyCategory(i=i, j=-1)

            for j, sub_cat_li_ in enumerate(main_cat_li_.css("ul li")):
                # self.logger.debug(f"spider yielding category {i} {j}")
                yield DummyCategory(i=i, j=j)
                # yielding an item results in the whole item pipeline being processed
                # until the next yield of this parse method is requested by the
                # scrapy framework

                # self.logger.debug("spider yielding article page link")
                yield response.follow(
                    sub_cat_li_.css("a")[0],
                    self.parse_article_page,
                    meta={"cat": f"{i} {j}", "page": 1},
                )
                # contrary to yielding a item, yielding a request will schedule
                # (but not execute synchronously) this request and immiediately
                # call for the next yield from this method
                # scheduling will acount for settings like DOWNLOAD_DELAY but wont
                # block the further execution of this parser
                # so the different parse methods are executed asynchornous
                # it also seemd that the order of the yielded requests might not get
                # accounted in the scheduling process but this shouldnt be an issue

                break  # execute only on first category for demonstration
            break

        self.logger.info(
            "Finished crawling category catalog. #############################################"
        )

    def parse_article_page(self, response: HtmlResponse):
        self.logger.debug(
            f"parsing articles from category {response.meta['cat']} ({response.url})"
        )

        articles_ = response.css(".aditem")
        for i, a in enumerate(articles_):
            self.logger.debug(f"yielding article {i}")
            yield DummyArticle(i)

        self.logger.info(
            f"Crawled {len(articles_)} articles from category {response.meta['cat']} ({response.url})."
        )

        # if len(articles_) == 0:
        #     open_in_browser(response)
        # self.logger.info(response.body)

        # yield response.follow(
        #     response.css("#srchrslt-pagination.pagination-next"),
        #     callback=self.parse_article_page,
        # )
