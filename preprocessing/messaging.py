import smtplib, ssl
from pathlib import Path
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
import time
import logging
import sys

import pandas as pd
from tabulate import tabulate
import schedule


def send_mail(sender_email, sender_password, receiver_email, subject, text):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    message.attach(MIMEText(text, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def send_status_mail(statistics_path, database_path, email_data):
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)

    con = sqlite3.connect(database_path)
    cur = con.cursor()
    n_articles = cur.execute("SELECT COUNT(*) FROM articles").fetchall()[0][0]

    df_stats = pd.read_csv(Path(statistics_path) / statistics_path)
    df_stats = df_stats[df_stats["start_timestamp"] > int(yesterday.timestamp())]
    df_stats["start_timestamp"] = df_stats["start_timestamp"].apply(
        lambda v: datetime.fromtimestamp(v).strftime("%H:%M:%S")
    )

    message = f"Report for {yesterday.strftime('%d.%m.%Y')}:<br><br>"
    message += f"articles fetched: {n_articles}<br><br>"
    message += f"{tabulate(df_stats, headers='keys', tablefmt='html')}"

    send_mail(
        email_data["sender_email"],
        email_data["sender_password"],
        email_data["receiver_email"],
        f"Ebk Bot Status {yesterday.strftime('%d.%m.%Y')}",
        message,
    )

    logging.info(f"Sended bot status report for {yesterday.strftime('%d.%m.%Y')}")


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    with open(Path(__file__).parent / "email_data.json", "r") as file:
        email_data = json.load(file)

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
    db_path = (
        Path(__file__).parent.parent
        / "data"
        / f"ebk_data__{yesterday.year}_{yesterday.month}_{yesterday.day}.db"
    )

    statistics_path = (
        Path(__file__).parent.parent
        / "webcrawler"
        / "ebk"
        / "log"
        / "crawling_statistics.csv"
    )

    schedule.every().day.at("01:00").do(
        send_status_mail, statistics_path, db_path, email_data
    )

    logging.info("Started schedule bot status email sending.")

    while True:
        schedule.run_pending()
        time.sleep(1)
