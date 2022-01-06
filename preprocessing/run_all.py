import logging
import sys
from datetime import datetime, timedelta
import time
from pathlib import Path
import json

import schedule

from messaging import send_status_mail
from preprocessing import drop_duplicates


def run_all():
    with open(Path(__file__).parent / "email_data.json", "r") as file:
        email_data = json.load(file)

    statistics_path = (
        Path(__file__).parent.parent
        / "webcrawler"
        / "ebk"
        / "log"
        / "crawling_statistics.csv"
    )

    def action():
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
        database_path = (
            Path(__file__).parent.parent
            / "data"
            / f"ebk_data__{yesterday.year}_{yesterday.month}_{yesterday.day}.db"
        )
        drop_duplicates(database_path)
        send_status_mail(statistics_path, database_path, email_data)

    schedule.every().day.at("01:00").do(action)

    logging.info("Started scheduled preprocessing.")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_all()
