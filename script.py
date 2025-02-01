import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
import time
from twilio.rest import Client

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SEARCH_BRANCH = os.getenv("SEARCH_BRANCH")
EMAIL_YEAR = os.getenv("EMAIL_YEAR")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
PERSONAL_WHATSAPP_NUMBER = os.getenv("PERSONAL_WHATSAPP_NUMBER")

processed_emails = set()


def send_whatsapp_message(message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{PERSONAL_WHATSAPP_NUMBER}",
            body=message
        )
        print("✅ WhatsApp message sent!")
    except Exception as e:
        print("❌ Failed to send WhatsApp message:", str(e))

def check_new_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        if not email_ids:
            print("No new emails.")
            return

        email_ids = [str(email_id, 'utf-8') for email_id in email_ids]

        for email_id in email_ids:
            if email_id in processed_emails:
                continue  

            status, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    msg = email.message_from_bytes(raw_email)

                    subject, encoding = decode_header(msg["Subject"] or "No Subject")[0]
                    if isinstance(subject, bytes) and encoding:
                        subject = subject.decode(encoding)

                    from_email = msg.get("From", "Unknown Sender")

                    email_date = msg["Date"]
                    parsed_date = email.utils.parsedate_to_datetime(email_date) if email_date else None
                    if parsed_date and str(parsed_date.year) != EMAIL_YEAR:
                        continue

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                                except:
                                    continue
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    if not body.strip():
                        continue

                    if SEARCH_BRANCH.lower() in body.lower():
                        print(f"📩 New Email - From: {from_email}, Subject: {subject}")

                        message = f"📩 New Email\nFrom: {from_email}\nSubject: {subject}\nDate: {email_date}\nPreview: {body[:300]}..."
                        send_whatsapp_message(message)

                        processed_emails.add(email_id)  

        mail.logout()

    except Exception as e:
        print("Error:", str(e))

check_new_emails()
