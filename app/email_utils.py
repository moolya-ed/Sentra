# ✅ app/email_utils.py

import smtplib
from email.message import EmailMessage
from .config import settings

def send_email(subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ALERT_RECEIVER
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    print(f"📧 Email sent: {subject} -> {settings.ALERT_RECEIVER}")
