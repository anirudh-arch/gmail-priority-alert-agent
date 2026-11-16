# Gmail Priority Alert Agent

A real-time Python notification agent built with FastAPI, Gmail API, and Google Cloud Pub/Sub that monitors incoming inbox messages from priority senders or organizations and triggers instant Windows desktop toast notifications.

## Tech Stack
- **Backend:** Python, FastAPI
- **APIs & Cloud:** Gmail API, Google Cloud Pub/Sub
- **Desktop Alerts:** Windows Toast Notifications (`winotify`)

## Prerequisites
- Windows 10/11 (required for desktop toast notifications)
- Python 3.10+
- A Google Cloud Project with **Gmail API** and **Cloud Pub/Sub API** enabled
- Ngrok (or a public HTTPS endpoint) to receive Pub/Sub push notifications

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/anirudh-arch/gmail-priority-alert-agent.git](https://github.com/anirudh-arch/gmail-priority-alert-agent.git)
   cd gmail-priority-alert-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add Google OAuth Credentials:**
   - Download your OAuth 2.0 Client ID JSON file from Google Cloud Console.
   - Rename it to `Credentials.json` and place it in the root project folder.

4. **Configure Priority Senders:**
   - Open `main.py` and update `ALLOWED_SENDERS` with the email addresses you want alerts for.

## Running the Agent

1. **Authenticate with Gmail (First-time setup):**
   ```bash
   python auth_gmail.py
   ```
   Sign in via your browser to generate `token.json`.

2. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --port 8000
   ```

3. **Expose your local port via Ngrok:**
   ```bash
   ngrok http 8000
   ```
   Configure your Google Cloud Pub/Sub push subscription endpoint to point to `<your-ngrok-url>/webhook` (or your configured webhook route).
