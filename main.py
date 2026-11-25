import base64
import json
from email.header import decode_header, make_header
from email.utils import parseaddr
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from whatsapp_notify import send_whatsapp_message


app = FastAPI()

# Email addresses we want to monitor
ALLOWED_SENDERS = [
    "sender1@example.com",
    "sender2@example.com",
    "sender3@example.com"
]

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TOKEN_FILE = Path("token.json")
STATE_FILE = Path("gmail_state.json")

# Prevent two notifications from processing the same cursor together
processing_lock = Lock()


def load_gmail_service():
    if not TOKEN_FILE.exists():
        raise RuntimeError("token.json is missing. Run py auth_gmail.py first.")

    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE), SCOPES
    )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError(
                "Gmail authentication is invalid. Run py auth_gmail.py again."
            )

    return build("gmail", "v1", credentials=creds)


def load_state():
    if not STATE_FILE.exists():
        raise RuntimeError(
            "gmail_state.json is missing. Run py auth_gmail.py first."
        )

    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )


def get_email_details(gmail, message_id):
    message = gmail.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "Subject"]
    ).execute()

    # Get the email headers
    headers = message.get("payload", {}).get("headers", [])

    header_map = {
        header["name"].lower(): header["value"]
        for header in headers
    }

    # Extract sender address
    from_header = header_map.get("from", "")
    sender_name, sender_email = parseaddr(from_header)

    # Decode subject if necessary
    raw_subject = header_map.get("subject", "(No subject)")
    subject = str(make_header(decode_header(raw_subject)))

    return {
        "sender_name": sender_name,
        "sender_email": sender_email.lower(),
        "subject": subject,
        "labels": message.get("labelIds", [])
    }


def process_gmail_notification(notification):

    with processing_lock:

        state = load_state()

        email_address = notification.get("emailAddress")
        notification_history_id = notification.get("historyId")

        if not email_address or not notification_history_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid Gmail notification"
            )

        if email_address.lower() != state["email_address"].lower():
            raise HTTPException(
                status_code=400,
                detail="Notification belongs to another mailbox"
            )

        last_history_id = str(state["history_id"])
        notification_history_id = str(notification_history_id)
        gmail = load_gmail_service()

        # Retrieve changes since the last saved history ID
        message_ids = set()
        page_token = None

        try:
            while True:
                params = {
                    "userId": "me",
                    "startHistoryId": last_history_id,
                    "historyTypes": ["messageAdded"],
                    "maxResults": 100
                }

                if page_token:
                    params["pageToken"] = page_token

                history_response = gmail.users().history().list(
                    **params
                ).execute()

                for record in history_response.get("history", []):
                    for added in record.get("messagesAdded", []):
                        message_id = added.get("message", {}).get("id")

                        if message_id:
                            message_ids.add(message_id)

                page_token = history_response.get("nextPageToken")

                if not page_token:
                    latest_history_id = str(
                        history_response.get(
                            "historyId", notification_history_id
                        )
                    )
                    break

        except HttpError as error:
            if error.resp.status == 404:
                print(
                    "WARNING: Gmail history cursor expired. "
                    "Re-register Gmail watch using py auth_gmail.py."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Gmail history cursor expired."
                )

            raise

        print(f"Found {len(message_ids)} newly added message(s).")

        # Retrieve and filter actual emails
        for message_id in message_ids:

            try:
                email_data = get_email_details(gmail, message_id)

            except HttpError as error:
                if error.resp.status == 404:
                    print("Message was no longer available. Skipping.")
                    continue
                raise

            # Only process messages currently in the Inbox
            if "INBOX" not in email_data["labels"]:
                continue

            sender = email_data["sender_email"]
            subject = email_data["subject"]

            if sender in ALLOWED_SENDERS:

                print("\n" + "=" * 45)
                print("IMPORTANT EMAIL DETECTED!")
                print("Sender:", email_data["sender_name"])
                print("Email:", sender)
                print("Subject:", subject)
                print("=" * 45 + "\n")

                # Prepare WhatsApp notification
                whatsapp_message = (
                    "Important New Email!\n\n"
                    f"From: {email_data['sender_name']}\n"
                    f"Email: {sender}\n"
                    f"Subject: {subject}"
                )

                # Send WhatsApp notification
                sent = send_whatsapp_message(whatsapp_message)

                if sent:
                    print("WhatsApp alert delivered to API successfully.")
                else:
                    print("Failed to send WhatsApp alert.")

            else:
                print("Ignored email from:", sender)

        # Update cursor after processing all new messages
        state["history_id"] = latest_history_id
        save_state(state)

        print("Gmail history updated:", latest_history_id)

        return {"status": "success"}


@app.post("/webhook")
def receive_gmail_notification(envelope: dict):

    if not isinstance(envelope, dict) or "message" not in envelope:
        raise HTTPException(
            status_code=400,
            detail="Invalid Pub/Sub envelope"
        )

    encoded_data = envelope["message"].get("data")

    if not encoded_data:
        raise HTTPException(
            status_code=400,
            detail="Missing Pub/Sub message data"
        )

    try:
        decoded_data = base64.urlsafe_b64decode(
            encoded_data + "=" * (-len(encoded_data) % 4)
        )

        notification = json.loads(decoded_data.decode("utf-8"))

    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid notification data"
        )

    print(
        "\nNew Gmail activity:",
        notification.get("emailAddress"),
        "History ID:",
        notification.get("historyId")
    )

    return process_gmail_notification(notification)
