import scrapy
import re


class CategorySpider(scrapy.Spider):
    name = "category"
    allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-katalog-orte.html"]
    start_urls = ["http://https://www.ebay-kleinanzeigen.de/s-katalog-orte.html/"]

    def parse(self, response):
        for main_cat_div_ in response.css(".contentbox .l-container-row"):
            main_cat_h2_ = main_cat_div_.css(".treelist-headline")
            main_cat_a_ = main_cat_h2_.css(".treelist-headline a")

            main_cat_url_name, main_cat_code = (
                main_cat_a_.attrib["href"].removeprefix("/").split("/")
            )
            main_cat_name = main_cat_a_.css("::text").get().strip()
            main_cat_articlecount = int(
                re.sub("\D", "", main_cat_h2_.css(".textlight::text").get())
            )

            for sub_cat_li_ in main_cat_div_.css("ul li"):
                sub_cat_a_ = sub_cat_li_.css("a")

                sub_cat_url_name, sub_cat_code = (
                    sub_cat_a_.attrib["href"].removeprefix("/").split("/")
                )
                sub_cat_name = sub_cat_a_.css("::text").get().strip()
                sub_cat_articlecount = int(
                    re.sub("\D", "", sub_cat_li_.css(".text-light").get())
                )
