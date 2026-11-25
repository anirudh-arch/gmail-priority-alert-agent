
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Locate the .env file in the project folder
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def send_whatsapp_message(message: str) -> bool:

    # Always reload the latest credentials from .env
    load_dotenv(ENV_FILE, override=True)

    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    to_number = os.getenv("WHATSAPP_TO_NUMBER", "").strip()
    api_version = os.getenv("WHATSAPP_API_VERSION", "v25.0").strip()

    # Check credentials
    if not all([access_token, phone_number_id, to_number]):
        print("Error: Missing WhatsApp credentials in .env")
        return False

    if not message or not message.strip():
        print("Error: WhatsApp message cannot be empty.")
        return False

    # WhatsApp Cloud API endpoint
    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/{phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

    except requests.RequestException as error:
        print("Network error while sending WhatsApp message:", error)
        return False

    # Read Meta's response
    try:
        result = response.json()

    except ValueError:
        print("Meta returned an invalid response.")
        print("HTTP Status:", response.status_code)
        return False

    # Handle unsuccessful requests
    if not response.ok:

        error = result.get("error", {}) if isinstance(result, dict) else {}

        error_code = error.get("code")
        error_message = error.get("message", "Unknown API error")
        error_subcode = error.get("error_subcode")
        fbtrace_id = error.get("fbtrace_id")

        print("\nWhatsApp API Error!")
        print("HTTP Status:", response.status_code)
        print("Error Code:", error_code)
        print("Error Type:", error.get("type"))
        print("Error Message:", error_message)

        if error_subcode:
            print("Error Subcode:", error_subcode)

        if fbtrace_id:
            print("Meta Trace ID:", fbtrace_id)

        if error_code == 190:
            print("\nAuthentication failed!")
            print("Meta rejected the access token.")
            print("Check its validity, expiry and app association.")
            print("Generate a fresh token if the current one is invalid.")

        elif error_code in (10, 200):
            print("\nPermission error!")
            print("Check WhatsApp Business API permissions.")

        print("WhatsApp message was not sent.")
        return False

    # Successful API response
    messages = result.get("messages", [])

    print("\nWhatsApp message accepted successfully!")

    if messages:
        print("Message ID:", messages[0].get("id"))
    else:
        print("No message ID was returned by Meta.")

    return True


# Test WhatsApp connection independently
if __name__ == "__main__":

    test_message = (
        "Hello! This is a test message "
        "from my Gmail Mail Alert Agent."
    )

    send_whatsapp_message(test_message)
