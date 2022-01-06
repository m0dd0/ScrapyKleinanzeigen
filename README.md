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

## Approximation of needed scraping interval
Each article page contains 25(+2) articles. 
We set the interval for crawling to DOWNLOAD_DELAY
If we directly restart the crawler after it has finished we can scrape at maximum
25/DOWNLOAD_DELAY articles per second.
If we want to catch all articles which get uploaded we need to adjust the DOWNLOAD_DELAY
depending on the uploaded article per second:
n_ups: uploaded articles per second
n_page: articles displayed on a single page (=25)
t_delay: DOWNLOAD_DELAY setting

t_delay = n_page/n_ups
n_ups = n_page/t_delay

n_ups [n_upm, n_uph]        t_delay
10 [600, 36.000]            25/10 = 2.5
40 [2.400, 144.000]         25/40 = 0.625
100 [6000, 360.000]         25/100 = 0.25 

Its open to test how many articles are uploaded per minute to see if it is realistic
to scrawl evers article.

## idea
Scrape more filtered metadata on article count in different regions/citys depending on category.

## ban protection
visitting website with browser manually: 141pages/1.33 min --> <1s Download Delay
but even if using a DOWNLOAD_DELAY of 3s > 1s scraper gets blocked
If scraper blocked website can still be accessed via browser BUT only if cookies are enabled in browser
--> Detection is done via cookies somehow
running scraper with cookies enabled and DOWNLOAD_DELAY=3 and "normal" USER_AGENT still results in blocking
--> Trying rotating proxies
Free proxies are 99% not wokring or way to slow
Paid proxy services are rather expensive (>20€/Monat)
--> Try scrapoxy with AWS

## Scraping abortion criterion
First idea was to detect if a number of articles have been scraped already. In theory, if this is the case 
we already visited them and therfore we also already visited the next/upcoming ones and we
can abort the crawling of this category.
However in praxis this didnt work: Even if we have a empty database we started detecting
multiple duplicates in the first run (which shouldnt be posible).
After some investigation it turned out that using the next page link will not automatically
give a full list of "fresh" articles. There are likely some articles shown in page
1 ansd 2. This effect appears only when using the scraper.
As an alternative the abortion is now only executed by the age of the visited articles:
The maximum age of artticles in a scrawling session is set so that there point of insertion
must eb bfeore the end of the last scrawling run + an delta of some minutes.
This will lead to some articles being scrawled multiple time but they are still 
detected as duplicates and will get dropped accordingly.

--> We scrawl once every n min. 
We set the maximum age of articles to (n+delta_upload)+2 min.
delta_upload ~ 2

n shouldnt be to low because in a less popular category this would mean that we scrawl
them without gaining any new (or only very few articles).
On the other side n shouldnt be to high to avoid missing articles in popular categories
because they are already on page 50+.
--> scrape every 10 minutes with an max age of 15min.

## performance
start_timestamp,duration,n_categories,total_pages,total_articles,pages_per_second,articles_per_second,max_pages,max_article,max_age,categories,seperate_business_ads,max_runtime
1640890539,292,266,532,14112,1.821917808219178,48.32876712328767,2,,,,True,
1640890857,154,266,266,7099,1.7272727272727273,46.0974025974026,1,,,,True,
1640891060,36,266,266,266,7.388888888888889,7.388888888888889,50,1,,,True, # --> processsing/writing articles is the limiting factor
1640891174,148,266,266,7099,1.7972972972972974,47.96621621621622,1,,,,True, # no json output --> makes no(less) difference
1640891407,140,266,266,7099,1.9,50.707142857142856,1,,,,True, # no writing to database --> makes lass difference
1640891749,131,266,266,7099,2.030534351145038,54.19083969465649,1,,,,True, # no loader logic
1640891954,35,266,266,7099,7.6,202.82857142857142,1,,,,True, # no css selectors --> much faster --> html parsing is the bottleneck
1640893443,36,266,266,7099,7.388888888888889,197.19444444444446,1,,,,True, # not using the loader for parsing html
1640893904,37,266,266,7100,7.1891891891891895,191.8918918918919,1,,,,True, # using no loader again and checked output --> works
1640894480,126,266,266,7100,2.111111111111111,56.34920634920635,1,,,,True, # using item based loader implementation --> loader has stull bad performance
1640906113,35,266,266,7100,7.6,202.85714285714286,1,,,,True, # using custom article and loader implementation
1640906038,36,266,266,7100,7.388888888888889,197.22222222222223,1,,,,True, # adding json output again
1640905953,39,266,266,7100,6.82051282051282,182.05128205128204,1,,,,True, # adding database output again

## dynamic crawl time
using a fixed interval at which all categories are crawled has a major downside:
For the most category we only get a few new articles which increases the number of
visited pages but doesnt provide many new articles but for some categories there
are so many articles published that we cant get all new articles within the first 
50 pages.

There are some possible solutions:
1.) Subdividing the crawl main pages by using state and "Art" for popular categoriews to increase the time between
crawls while still getting all articles. --> we still need to crawl every hour and the crawler
runs very long which might lead to a high number of duplicates
2.) Run a seperate crawler for each category and schedule them depending on the number 
of new articles or visited pages.
After a the crawler has run for articles between last run and now given time they save how many
pages they had to visit to get all new articles.
If the number of pages is one the 
The number of pages and the category and the start time is saved to the database.
A scheduler in a seperate process checks the database every minute or so.
To 

How do we communicate between the spiders and the scheduler?
    - using a seperate database
    - using zeroMQ