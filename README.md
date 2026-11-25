
# Gmail Mail Alert Agent

A Python-based automation agent that monitors incoming Gmail messages from selected senders and automatically sends WhatsApp notifications.

## Features

- Monitors incoming Gmail messages.
- Filters emails using a customizable sender allowlist.
- Detects new email activity through Google Cloud Pub/Sub.
- Processes notifications using FastAPI webhooks.
- Sends WhatsApp alerts containing the sender's name, email address, and subject.
- Loads API credentials securely using environment variables.

## Technologies Used

- Python
- Gmail API
- Google Cloud Pub/Sub
- FastAPI
- ngrok
- Meta WhatsApp Cloud API
- OAuth 2.0

## Project Structure

```text
gmail-priority-alert-agent/
│
├── main.py
├── auth_gmail.py
├── whatsapp_notify.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

## Prerequisites

- Python 3.10 or later
- Google Cloud Project
- Gmail API enabled
- Google Cloud Pub/Sub configured
- Meta Developer Account
- WhatsApp Cloud API configured
- ngrok installed

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/anirudh-arch/gmail-priority-alert-agent.git
   cd gmail-priority-alert-agent
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file by copying `.env.example`.

4. Configure the required environment variables in `.env`:

   - GOOGLE_CLOUD_PROJECT_ID
   - WHATSAPP_ACCESS_TOKEN
   - WHATSAPP_PHONE_NUMBER_ID
   - WHATSAPP_TO_NUMBER
   - WHATSAPP_API_VERSION

5. Download your Google OAuth 2.0 Desktop application credentials and save the file as `Credentials.json` in the project folder.

## Google Cloud Configuration

1. Enable the Gmail API and Google Cloud Pub/Sub API.
2. Create a Pub/Sub topic named `gmail-notifications`.
3. Configure the required Gmail push notification permissions.
4. Create a push subscription pointing to your public webhook URL.

## Running the Agent

1. Authenticate with Gmail and register push notifications:

   ```bash
   python auth_gmail.py
   ```

2. Start the FastAPI server:

   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. Open another terminal and start ngrok:

   ```bash
   ngrok http 8000
   ```

4. Configure your Google Cloud Pub/Sub push subscription to use:

   ```text
   https://YOUR_NGROK_URL/webhook
   ```

5. Add the email addresses you want to monitor to `ALLOWED_SENDERS` in `main.py`.

Once configured, the agent detects incoming emails from approved senders and sends WhatsApp notifications automatically.

## Testing WhatsApp

You can independently test the WhatsApp integration using:

```bash
python whatsapp_notify.py
```

## Security Notes

- Never upload `.env`, `Credentials.json`, or `token.json`.
- Keep API tokens and OAuth credentials private.
- Use `.env.example` as a configuration template.
- Do not expose personal email addresses or phone numbers in public source code.

## Limitations

- The local application and ngrok tunnel must remain running.
- Gmail push notifications require periodic watch renewal.
- WhatsApp test numbers have testing restrictions.
- Messages outside the 24-hour customer service window require approved WhatsApp message templates.

## Author

Developed as a Python automation project.
