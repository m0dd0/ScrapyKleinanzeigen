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
