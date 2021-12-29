import logging
from scrapy import logformatter

from .items import EbkArticle


class CustomLogFormatter(logformatter.LogFormatter):
    def crawled(self, request, response, spider):
        res = super().crawled(request, response, spider)
        res["level"] = logging.INFO
        return res

    def dropped(self, item, exception, response, spider):
        res = super().dropped(item, exception, response, spider)
        res["level"] = logging.INFO
        # res["msg"] = "Dropped: %(exception)s" + os.linesep + "%(item)s"
        # if isinstance(item, EbkArticle):
        #     item_name_encoded = item.name.encode("utf-8")
        #     res["msg"] = (
        #         "Dropped: %(exception)s"
        #         + f"EbkArticle (category: {item.sub_category}, name: '{item_name_encoded}')"
        #     )
        return res

        # TODO fix this error
        # Traceback (most recent call last):
        #   File "c:\users\""\appdata\local\programs\python\python39\lib\logging\__init__.py", line 1082, in emit
        #     stream.write(msg + self.terminator)
        #   File "c:\users\""\appdata\local\programs\python\python39\lib\encodings\cp1252.py", line 19, in encode
        #     return codecs.charmap_encode(input,self.errors,encoding_table)[0]
        # UnicodeEncodeError: 'charmap' codec can't encode character '\u2606' in position 108: character maps to <undefined>
        # Call stack:
        #   File "c:\users\""\appdata\local\programs\python\python39\lib\runpy.py", line 197, in _run_module_as_main
        #     return _run_code(code, main_globals, None,
        #   File "c:\users\""\appdata\local\programs\python\python39\lib\runpy.py", line 87, in _run_code
        #     exec(code, run_globals)
        #   File "D:\""\venv\Scripts\scrapy.exe\__main__.py", line 7, in <module>
        #     sys.exit(execute())
        #   File "D:\""\venv\lib\site-packages\scrapy\cmdline.py", line 145, in execute
        #     _run_print_help(parser, _run_command, cmd, args, opts)
        #   File "D:\""\venv\lib\site-packages\scrapy\cmdline.py", line 100, in _run_print_help
        #     func(*a, **kw)
        #   File "D:\""\venv\lib\site-packages\scrapy\cmdline.py", line 153, in _run_command
        #     cmd.run(args, opts)
        #   File "D:\""\venv\lib\site-packages\scrapy\commands\crawl.py", line 27, in run
        #     self.crawler_process.start()
        #   File "D:\""\venv\lib\site-packages\scrapy\crawler.py", line 327, in start
        #     reactor.run(installSignalHandlers=False)  # blocking call
        #   File "D:\""\venv\lib\site-packages\twisted\internet\base.py", line 1318, in run
        #     self.mainLoop()
        #   File "D:\""\venv\lib\site-packages\twisted\internet\base.py", line 1328, in mainLoop
        #     reactorBaseSelf.runUntilCurrent()
        #   File "D:\""\venv\lib\site-packages\twisted\internet\base.py", line 994, in runUntilCurrent
        #     call.func(*call.args, **call.kw)
        #   File "D:\""\venv\lib\site-packages\twisted\internet\task.py", line 682, in _tick
        #     taskObj._oneWorkUnit()
        #   File "D:\""\venv\lib\site-packages\twisted\internet\task.py", line 528, in _oneWorkUnit
        #     result = next(self._iterator)
        #   File "D:\""\venv\lib\site-packages\scrapy\utils\defer.py", line 74, in <genexpr>
        #     work = (callable(elem, *args, **named) for elem in iterable)
        #   File "D:\""\venv\lib\site-packages\scrapy\core\scraper.py", line 197, in _process_spidermw_output
        #     dfd.addBoth(self._itemproc_finished, output, response, spider)
        #   File "D:\""\venv\lib\site-packages\twisted\internet\defer.py", line 539, in addBoth
        #     return self.addCallbacks(
        #   File "D:\""\venv\lib\site-packages\twisted\internet\defer.py", line 478, in addCallbacks
        #     self._runCallbacks()
        #   File "D:\""\venv\lib\site-packages\twisted\internet\defer.py", line 858, in _runCallbacks
        #     current.result = callback(  # type: ignore[misc]
        #   File "D:\""\venv\lib\site-packages\scrapy\core\scraper.py", line 243, in _itemproc_finished
        #     logger.log(*logformatter_adapter(logkws), extra={'spider': spider})
        # Message: 'Dropped: %(exception)s\r\n%(item)s'
        # Arguments: {'exception': DropItem('Dropped duplicated article.'), 'item': EbkArticle(name='☆ Seni Soft Basic Betteinlagen ☆ Inkontinenz ☆ 90x60 cm ☆', price=10, negotiable=False, postal_code='89250', timestamp=1640784840, description='Bietet Betteinlagen für die Pflege. (Inkontinenz)\n\n5 Kartone mit je 50 Einlagen. (90×60cm)\n\nIch', sendable=True, offer=True, tags=[], main_category='Dienstleistungen', sub_category='Altenpflege', is_business_ad=None, image_link=None, pro_shop_link=None, top_ad=False, highlight_ad=False, link='https://www.ebay-kleinanzeigen.de/s-anzeige/-seni-soft-basic-betteinlagen-inkontinenz-90x60-cm-/1973652485-236-6688')}2021-12-29 14:50:10 [scrapy.core.scraper] INFO: Dropped: Dropped duplicated article.
        # EbkArticle(name='☆ Seni Soft Basic Betteinlagen ☆ Inkontinenz ☆ 90x60 cm ☆', price=10, negotiable=False, postal_code='89250', timestamp=1640784840, description='Bietet Betteinlagen für die Pflege. (Inkontinenz)\n\n5 Kartone mit je 50 Einlagen. (90×60cm)\n\nIch', sendable=True, offer=True, tags=[], main_category='Dienstleistungen', sub_category='Altenpflege', is_business_ad=None, image_link=None, pro_shop_link=None, top_ad=False, highlight_ad=False, link='https://www.ebay-kleinanzeigen.de/s-anzeige/-seni-soft-basic-betteinlagen-inkontinenz-90x60-cm-/1973652485-236-6688')
        # 2021-12-29 14:50:10 [scrapy.core.scraper] INFO: Dropped: Dropped duplicated article.
        # EbkArticle(name='Bama Schuhe gr 25', price=5, negotiable=False, postal_code='97422', timestamp=1640785620, description='Sehr guter gebrauchter Zustand.\nVersand bei Übernahme der Kosten möglich. (5€)\nPrivatverkauf daher', sendable=True, offer=True, tags=[], main_category='Familie, Kind & Baby', sub_category='Baby- & Kinderschuhe', is_business_ad=None, image_link=None, pro_shop_link=None, top_ad=False, highlight_ad=False, link='https://www.ebay-kleinanzeigen.de/s-anzeige/bama-schuhe-gr-25/1973670950-19-6858')
