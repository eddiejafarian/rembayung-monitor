import requests
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------- SETTINGS ----------
STATE_FILE = "last_alert.txt"
COOLDOWN = 60 * 60 * 2  # 2 hours
BOOKING_URL = "https://reservation.umai.io/en/widget/rembayung"
API_URL = "https://reservation.umai.io/api/venues/rembayung/availability"
# ------------------------------


def booking_available():
    """Check UMAI reservation API for available slots"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        r = requests.get(API_URL, headers=headers, timeout=30)

        if r.status_code != 200:
            print("Bad response:", r.status_code)
            return False

        data = r.json()

        # Look for any slot > 0
        for day in data.get("availability", []):
            for slot in day.get("timeslots", []):
                if slot.get("available", 0) > 0:
                    print("Available slot detected:", day.get("date"), slot.get("time"))
                    return True

        return False

    except Exception as e:
        print("API error:", e)
        return False


def last_alert_time():
    if not os.path.exists(STATE_FILE):
        return 0

    with open(STATE_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0


def save_alert_time(timestamp):
    with open(STATE_FILE, "w") as f:
        f.write(str(timestamp))


def send_email():
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    subject = "Rembayung Reservation Available!"
    body = f"""
Rembayung reservation slot detected.

BOOK NOW:
{BOOKING_URL}

(This alert will pause for 2 hours after sending.)
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

    if booking_available():
        last_time = last_alert_time()
        elapsed = now - last_time

        if elapsed >= COOLDOWN:
            print("Sending alert email...")
            send_email()
            save_alert_time(now)
        else:
            print(f"Cooldown active. Next alert allowed in {(COOLDOWN-elapsed)//60} minutes")
    else:
        print("No slots available")
