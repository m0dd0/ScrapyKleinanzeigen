import scrapy


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    allowed_domains = ["https://www.ebay-kleinanzeigen.de/s-suchen.html"]
    url_base = (
        "https://www.ebay-kleinanzeigen.de/s-autos/anbieter:gewerblich/seite:{}/c216"
    )
    # page_number = 0

    start_urls = [
        "https://www.ebay-kleinanzeigen.de/s-autos/anbieter:gewerblich/seite:1/c216",
        # "https://www.ebay-kleinanzeigen.de/s-autoteile-reifen/anbieter:gewerblich/seite:1/c223",
        # "https://www.ebay-kleinanzeigen.de/s-boote-bootszubehoer/anbieter:gewerblich/c211"
    ]

    def start_requests(self):
        urls = [
            "https://www.ebay-kleinanzeigen.de/s-reparaturen-dienstleistungen/c280"
            "http://quotes.toscrape.com/page/1/",
            "http://quotes.toscrape.com/page/2/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for i in range(50):
            # response.
            yield ...
            yield
            raise CloseSpider
        # response.
        # page = response.url.split("/")[-2]
        # filename = f'quotes-{page}.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # self.log(f'Saved file {filename}')
