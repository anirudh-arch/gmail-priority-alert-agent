import json
from pathlib import Path
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail read-only permission
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Google Cloud project and Pub/Sub topic
PROJECT_ID = "gmail-whatsapp-agent-514409"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/gmail-notifications"

CREDENTIALS_FILE = "Credentials.json"
TOKEN_FILE = "token.json"


def get_gmail_credentials():
    creds = None

    # Load previously saved authentication
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )

    # Refresh or request new authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        Path(TOKEN_FILE).write_text(
            creds.to_json(), encoding="utf-8"
        )

    return creds


def main():
    try:
        print("Connecting to Gmail...")

        creds = get_gmail_credentials()

        gmail = build("gmail", "v1", credentials=creds)

        # Check which Gmail account is connected
        profile = gmail.users().getProfile(
            userId="me"
        ).execute()

        print("Authenticated successfully!")
        print("Gmail account:", profile["emailAddress"])

        # Register Gmail push notifications
        request_body = {
            "topicName": TOPIC_NAME,
            "labelIds": ["INBOX"],
            "labelFilterBehavior": "INCLUDE"
        }

        response = gmail.users().watch(
            userId="me",
            body=request_body
        ).execute()
        
        # Save Gmail history ID for future notifications
        state = {
            "history_id": response["historyId"],
            "email_address": profile["emailAddress"],
            "expiration": response["expiration"]
        }

        Path("gmail_state.json").write_text(
            json.dumps(state, indent=2),
            encoding="utf-8"
        )

        print("Gmail state saved successfully!")
        expiration = int(response["expiration"]) / 1000

        expiry_date = datetime.fromtimestamp(
            expiration, tz=timezone.utc
        )

        print("\nGmail notifications activated!")
        print("History ID:", response["historyId"])
        print("Watch expires:", expiry_date)

    except FileNotFoundError as error:
        print("Missing credentials file:", error)

    except HttpError as error:
        print("Gmail API error:", error)


if __name__ == "__main__":
    main()
