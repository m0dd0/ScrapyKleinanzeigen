# ScrapyKleinanzeigen
## Design
### article attributes
- name                  the name of the article
- price                 the price of the article, if "zu verschenken" price is set to 0, sometimes no price is given (even if it seems to be impossible to create an article without price, price is only "VB" or nothing at all) in this case price is set to none
- negotiable            if the proce was marked with 
- postal_code           the postal code of the article
- timestamp             the time of creation of this article in seconds after 1970 (however only minutely accuracy provided)
- description           the intro of the description of the article 
- dispatchable          if there is the "Versand möglich" tag in the tags
- offer                 if its an offer or an search (detemined by the existance of the "gesuch" tag)
- tags                  a list of tags other than "gesuch" or "Versand möglich"
- category              the main category this article belongs to (can be found out only by using the corresponding serach url)
- sub_category          the sub category this article belongs to (can be found out only by using the corresponding serach url)
- commercial_offer      if this article is offered by an shop etc (can be found out only by using the corresponding serach url)
- pro_shop_link         some commercial articles provide an link to their shop (together with a "pro" tag), none in the most cases
- top_article           if the article is marked with the top flag
- highlight_article     if the article is marked as highlighted
- image                 the thumbnail of the article

To get all the needed categories we need to search by (sub)category and commercial/private offer.

One spider is responsible for scraping the articles of one category.
Each spider iterates over the pages [1:50] until multiple duplicates are found.
Scheduling the spiders every minute should be enough to catch every article even in 
the most popular categories.
To avoid intensive lookup for each article if its already saved, the articles of 
each crawling session getting saved seperately so we only need to query them.

We should also save some metadata for the crawling session itself like:
- category and commercial/private
- what time
- how many new articles fetched / how many pages visited
With this information we can later adapt the intervals of the crawlers to minimize
traffic or to ensure that all articles got scraped.

A scraper which checks for new categories and updates the json should be run every
day etc.

