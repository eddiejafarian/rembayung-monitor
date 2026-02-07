import requests
import smtplib
import os
import time

URL = "https://reservation.umai.io/en/widget/rembayung"
KEYWORD = "We are fully booked"

COOLDOWN = 60 * 60 * 2  # 2 hours (seconds)
STATE_FILE = "last_alert.txt"


def page_available():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(URL, headers=headers, timeout=30)
    html = r.text

    return KEYWORD not in html


def last_alert_time():
    if not os.path.exists(STATE_FILE):
        return 0

    with open(STATE_FILE, "r") as f:
        return int(f.read().strip())


def save_alert_time(timestamp):
    with open(STATE_FILE, "w") as f:
        f.write(str(timestamp))


def send_email():
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    subject = "🚨 REMBAYUNG BOOKING OPEN!"
    body = f"""Booking may be available!

The page no longer shows "{KEYWORD}"

Go NOW:
{URL}
"""

    message = f"""From: {sender}
To: {receiver}
Subject: {subject}

{body}
"""

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, message)


if __name__ == "__main__":
    now = int(time.time())

    if page_available():
        last_time = last_alert_time()
        elapsed = now - last_time

        if elapsed >= COOLDOWN:
            print("Booking OPEN — sending email")
            send_email()
            save_alert_time(now)
        else:
            print(f"Booking open but in cooldown ({elapsed//60} minutes passed)")
    else:
        print("Still fully booked")
