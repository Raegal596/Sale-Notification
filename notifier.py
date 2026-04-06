import os
import json
import smtplib
from email.message import EmailMessage
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# Email Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

# Config file configuration
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
TO_EMAIL = os.getenv("TO_EMAIL")

try:
    with open('config.json', 'r') as f:
        config_data = json.load(f)
        if "TO_PHONE_NUMBER" in config_data:
            TO_PHONE_NUMBER = config_data["TO_PHONE_NUMBER"]
        if "TO_EMAIL" in config_data:
            TO_EMAIL = config_data["TO_EMAIL"]
except (FileNotFoundError, json.JSONDecodeError):
    pass

sms_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None
sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY) if SENDGRID_API_KEY else None


def format_listings_text(listings: list[dict], truncate_length: int = None) -> str:
    message_body = f"Found {len(listings)} new listings!\n\n"
    for listing in listings:
        message_body += f"- {listing['title']} ({listing['price']})\n{listing['url']}\n\n"
        
    if truncate_length and len(message_body) > truncate_length:
        message_body = message_body[:truncate_length - 25] + "...\n(Message truncated)"
    
    return message_body


def format_listings_html(listings: list[dict]) -> str:
    html = f"<h3>Found {len(listings)} new listings!</h3><ul>"
    for listing in listings:
        html += f'<li><a href="{listing["url"]}">{listing["title"]}</a> - <strong>{listing["price"]}</strong></li>'
    html += "</ul>"
    return html


def send_bulk_sms_notification(listings: list[dict], to_phone_number: str = None):
    target_number = to_phone_number or TO_PHONE_NUMBER
    if not sms_client or not target_number or not TWILIO_FROM_NUMBER:
        return False
        
    message_body = format_listings_text(listings, truncate_length=1500)
    
    try:
        message = sms_client.messages.create(
            body=message_body,
            from_=TWILIO_FROM_NUMBER,
            to=target_number
        )
        print(f"Bulk SMS sent successfully: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send bulk SMS: {e}")
        return False


def send_bulk_email_sendgrid(listings: list[dict]):
    if not sendgrid_client or not TO_EMAIL or not FROM_EMAIL:
        return False

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject=f"{len(listings)} New Listings Found!",
        html_content=format_listings_html(listings)
    )
    
    try:
        response = sendgrid_client.send(message)
        print(f"SendGrid email sent successfully. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send SendGrid email: {e}")
        return False


def send_bulk_email_smtp(listings: list[dict]):
    if not SMTP_USER or not SMTP_PASSWORD or not TO_EMAIL or not FROM_EMAIL:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"{len(listings)} New Listings Found!"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    
    msg.set_content(format_listings_text(listings))
    msg.add_alternative(format_listings_html(listings), subtype='html')

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print("SMTP email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send SMTP email: {e}")
        return False


def send_notifications(listings: list[dict], to_phone_number: str = None):
    if not listings:
        return
        
    # Send SMS if configured
    send_bulk_sms_notification(listings, to_phone_number)
    
    # Send Email via SendGrid if configured, otherwise try SMTP
    if sendgrid_client:
        send_bulk_email_sendgrid(listings)
    elif SMTP_USER and SMTP_PASSWORD:
        send_bulk_email_smtp(listings)
    else:
        if not sms_client:
            print("Warning: No notification methods configured. Please check .env and config.")

if __name__ == "__main__":
    test_listing = {
        'title': 'Test Item',
        'price': '$100',
        'url': 'https://example.com',
        'source': 'test'
    }
    send_notifications([test_listing])
