from time import time
import scrapy
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from ..items import DummyArticle, DummyCategory


class SearchSpider(scrapy.Spider):
    name = "search_spider_dummy"
    # allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    # start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def __init__(self, *args, **kwargs):
        self.finished_categories = []
        super().__init__(*args, **kwargs)

    def set_attr_from_pipeline(self, attr):
        pass
        # print(f"spider set atr from pipeline: {attr}")

    def start_requests(self):
        start_url = "https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"
        yield scrapy.Request(url=start_url, callback=self.parse_category_catalog)

    def parse_category_catalog(self, response: HtmlResponse):
        for i, main_cat_li_ in enumerate(response.css(".contentbox .l-container-row")):
            # print(f"spider main cat: {i}")
            yield DummyCategory(i=i, j=-1)

            for j, sub_cat_li_ in enumerate(main_cat_li_.css("ul li")):
                # print(f"spider sub cat: {i} {j}")
                yield DummyCategory(i=i, j=j)
                # yielding an item results in the whole item pipeline being processed
                # until the next yield of this parse method is requested by the
                # scrapy framework

                # print("spider yield article page link")
                yield response.follow(
                    sub_cat_li_.css("a")[0],
                    self.parse_article_page,
                    meta={"cat": f"{i} {j}"},
                )
                # contrary to yielding a item, yielding a request will schedule
                # (but not execute synchronously) this request and immiediately
                # call for the next yield from this method
                # scheduling will acount for settings like DOWNLOAD_DELAY but wont
                # block the further execution of this parser
                # so the different parse methods are executed asynchornous
                # it also seemd that the order of the yielded requests might not get
                # accounted in the scheduling process but this shouldnt be an issue

    def parse_article_page(self, response: HtmlResponse):
        # print(f"parse article page from category {response.meta['cat']}")
        for i, article_ in enumerate(response.css(".aditem")):
            # print(f"spider article: {i} (cat: {response.meta['cat']})")
            yield DummyArticle(i)

        # yield response.follow(
        #     response.css("#srchrslt-pagination.pagination-next"),
        #     callback=self.parse_article_page,
        # )
