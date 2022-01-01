import smtplib, ssl
from pathlib import Path
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from tabulate import tabulate


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


def send_status_mail(email_data):
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)

    db_path = (
        Path(__file__).parent.parent
        / "data"
        / f"ebk_data__{yesterday.year}_{yesterday.month}_{yesterday.day}.db"
    )
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    n_articles = cur.execute("SELECT COUNT(*) FROM articles").fetchall()[0][0]

    log_path = (
        Path(__file__).parent.parent
        / "webcrawler"
        / "ebk"
        / "log"
        / "crawling_statistics.csv"
    )
    df_stats = pd.read_csv(Path(log_path) / log_path)
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


if __name__ == "__main__":
    with open(Path(__file__).parent / "email_data.json", "r") as file:
        email_data = json.load(file)
    send_status_mail(email_data)
