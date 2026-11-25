
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)


# Gmail read-only permission
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "").strip()

# Local credential and state files
CREDENTIALS_FILE = BASE_DIR / "Credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
STATE_FILE = BASE_DIR / "gmail_state.json"


def get_gmail_credentials():

    creds = None

    # Load previously saved authentication
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    # Refresh or request new authentication
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    elif not creds or not creds.valid:

        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Credentials.json is missing. "
                "Download your Google OAuth credentials "
                "and place them in the project folder."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )

        creds = flow.run_local_server(port=0)

    # Save updated authentication
    TOKEN_FILE.write_text(
        creds.to_json(),
        encoding="utf-8"
    )

    return creds


def main():

    if not PROJECT_ID:
        print(
            "Error: GOOGLE_CLOUD_PROJECT_ID is missing "
            "from your .env file."
        )
        return

    topic_name = (
        f"projects/{PROJECT_ID}/topics/gmail-notifications"
    )

    try:

        print("Connecting to Gmail...")

        creds = get_gmail_credentials()

        gmail = build(
            "gmail",
            "v1",
            credentials=creds
        )

        # Check connected Gmail account
        profile = gmail.users().getProfile(
            userId="me"
        ).execute()

        print("Authenticated successfully!")
        print("Gmail account:", profile["emailAddress"])

        # Register Gmail push notifications
        request_body = {
            "topicName": topic_name,
            "labelIds": ["INBOX"],
            "labelFilterBehavior": "INCLUDE"
        }

        response = gmail.users().watch(
            userId="me",
            body=request_body
        ).execute()

        # Save Gmail history information
        state = {
            "history_id": response["historyId"],
            "email_address": profile["emailAddress"],
            "expiration": response["expiration"]
        }

        STATE_FILE.write_text(
            json.dumps(state, indent=2),
            encoding="utf-8"
        )

        print("Gmail state saved successfully!")

        expiration = int(response["expiration"]) / 1000

        expiry_date = datetime.fromtimestamp(
            expiration,
            tz=timezone.utc
        )

        print("\nGmail notifications activated!")
        print("History ID:", response["historyId"])
        print("Watch expires:", expiry_date)

    except FileNotFoundError as error:
        print("Missing credentials file:", error)

    except HttpError as error:
        print("Gmail API error:", error)

    except Exception as error:
        print("Unexpected error:", error)


if __name__ == "__main__":
    main()
