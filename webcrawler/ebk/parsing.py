import re
from datetime import datetime, timedelta


def integer_from_string(string: str):
    res = re.sub("\D", "", string)
    if res == "":
        return None
    if len(res) > 1:
        res = res.removeprefix("0")
    return int(res)


def get_article_datetime(datestring: str):
    datestring = datestring.lower().strip()

    # in case the article is a topad only empty string are contained in the topright div
    # also sometimes two strings are in the div from ahich one is only a "\n"
    # in this case abort further parsing by returning None
    if datestring == "":
        return None

    if re.match("gestern|heute.*", datestring):
        yesterday = datestring.startswith("gestern")
        hour, minute = divmod(integer_from_string(datestring), 100)

        current_datetime = datetime.now()
        article_datetime = datetime(
            current_datetime.year,
            current_datetime.month,
            current_datetime.day,
            hour,
            minute,
            0,
            0,
        )
        if yesterday:
            article_datetime = article_datetime - timedelta(days=1)

        return article_datetime

    else:
        return datetime.strptime(datestring, "%d.%m.%Y")


def eval_timestamp_str(timestamp_str):
    dt = get_article_datetime(timestamp_str)
    if dt:
        return int(dt.timestamp())
    return None


def eval_price_string(price_string):
    if not price_string:
        return None
    if "zu verschenken" in price_string.lower():
        return 0
    return integer_from_string(price_string)
