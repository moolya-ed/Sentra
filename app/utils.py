# sentra/app/utils.py

from twilio.rest import Client
from .config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    SMS_RECEIVER
)

def calculate_request_size(headers: dict) -> int:
    return sum(len(k) + len(v) for k, v in headers.items())

def send_sms_alert(message: str):
    """
    Send an SMS using Twilio.
    Reads credentials from config.py (.env)
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, SMS_RECEIVER]):
        print("❌ Twilio settings are incomplete. SMS not sent.")
        return

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=SMS_RECEIVER
        )
        print(f"✅ SMS sent successfully. SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
