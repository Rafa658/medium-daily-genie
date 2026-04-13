# Medium Daily Genie

Python prototype that reads Gmail emails received within the last 1 day from `Medium Daily Digest <noreply@medium.com>`, extracts the article links from the digest, prints a Markdown summary in the terminal, and sends the same report by email.

## Structure

- `main.py`: prototype entry point
- `src/medium_daily_digest/services/`: Gmail authentication, email reading, report generation, and email sending
- `src/medium_daily_digest/utils/`: link extraction helpers
- `credentials/google_oauth_client.json` or a root-level `client_secret_*.json`: Google OAuth credentials
- `credentials/token.json`: token generated locally after the first authentication

## How to Run

1. Enable the Gmail API in a Google Cloud project.
2. Create an OAuth Client ID of type `Desktop app`.
3. Download the JSON file and save it as `credentials/google_oauth_client.json`, or keep the `client_secret_*.json` file in the project root.
4. Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

5. Run:

```bash
.venv/bin/python main.py
```

On the first run, your browser will open for Google account authentication and a `token.json` file will be saved locally.
