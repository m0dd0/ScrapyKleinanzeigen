import sqlite3
import logging
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
from typing import Tuple

import schedule


def drop_duplicates(
    database_path: Path, duplicate_columns: Tuple[str] = ("link", "sub_category")
):
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    cur.execute(
        f"""
        DELETE FROM articles
        WHERE rowid NOT IN (
            SELECT MIN(rowid) 
            FROM articles 
            GROUP BY {','.join(duplicate_columns)}
        )"""
    )
    con.commit()
    cur.execute("VACUUM")
    con.commit()

    logging.info(f"Dropped duplicates for database '{database_path.stem}'.")


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
    db_path = (
        Path(__file__).parent.parent
        / "data"
        / f"ebk_data__{yesterday.year}_{yesterday.month}_{yesterday.day}.db"
    )

    schedule.every().day.at("21:57").do(drop_duplicates, db_path)

    logging.info("Started scheduled removal of duplicates.")

    while True:
        schedule.run_pending()
        time.sleep(1)
