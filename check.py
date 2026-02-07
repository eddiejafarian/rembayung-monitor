import os
import time
import smtplib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = "https://reservation.umai.io/en/widget/rembayung"
KEYWORD = "We are fully booked"

STATE_FILE = "last_alert.txt"
COOLDOWN = 60 * 60 * 2  # 2 hours


def page_has_full_text():
    """Open real browser and read page text"""

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(URL)

        # VERY IMPORTANT: allow javascript to load booking widget
        time.sleep(15)

        page_text = driver.page_source

        if KEYWORD in page_text:
            print("Still fully booked")
            return True
        else:
            print("Booking text missing -> possible opening")
            return False

    finally:
        driver.quit()


def last_alert_time():
    if not os.path.exists(STATE_FILE):
        return 0

    with open(STATE_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0


def save_alert_time(ts):
    with open(STATE_FILE, "w") as f:
        f.write(str(ts))


def send_email():
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    subject = "REMBAYUNG BOOKING MAY BE OPEN"
    body = f"""
The page no longer shows "We are fully booked".

Check immediately:
{URL}
"""

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, msg.as_string())


# ---------- MAIN ----------
if __name__ == "__main__":
    now = int(time.time())

    fully_booked = page_has_full_text()

    if not fully_booked:
        last_time = last_alert_time()
        if now - last_time >= COOLDOWN:
            print("Sending email alert")
            send_email()
            save_alert_time(now)
        else:
            print("Cooldown active")
    else:
        print("No action")
