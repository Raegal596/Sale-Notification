import os
import json
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# Assuming the config has the TO number
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
try:
    with open('config.json', 'r') as f:
        config_data = json.load(f)
        if "TO_PHONE_NUMBER" in config_data:
            TO_PHONE_NUMBER = config_data["TO_PHONE_NUMBER"]
except (FileNotFoundError, json.JSONDecodeError):
    pass

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

def send_bulk_sms_notification(listings: list[dict]):
    """
    Sends a single SMS notification containing details of multiple listings.
    """
    if not client:
        print("Warning: Twilio client not configured. Skipping SMS.")
        return False
        
    if not TO_PHONE_NUMBER or not TWILIO_FROM_NUMBER:
        print("Warning: Missing Twilio phone numbers in config. Skipping SMS.")
        return False
        
    if not listings:
        return False
        
    message_body = f"Found {len(listings)} new listings!\n\n"
    for listing in listings:
        # Keep each listing concise to fit more in the SMS
        message_body += f"- {listing['title']} ({listing['price']})\n{listing['url']}\n\n"
        
    # Twilio has a character limit, we will truncate the body if it's too long
    if len(message_body) > 1500:
        message_body = message_body[:1480] + "...\n(Message truncated)"
    
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_FROM_NUMBER,
            to=TO_PHONE_NUMBER
        )
        print(f"Bulk SMS sent successfully: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send bulk SMS: {e}")
        return False

if __name__ == "__main__":
    # Test notification
    test_listing = {
        'title': 'Test Item',
        'price': '$100',
        'url': 'https://example.com',
        'source': 'test'
    }
    send_bulk_sms_notification([test_listing])
