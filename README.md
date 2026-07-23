# Edoofa Conversation Audit Prototype

This prototype is a simple Streamlit app for uploading WhatsApp-style conversation transcripts and generating an audit report of counselor communication quality.

## Audit Framework

1. Tone & Empathy
2. Consistency & Follow-through
3. Clarity & Transparency
4. Student-Centric Focus
5. Pressure & Sales Intensity

## How it works

- Upload one or more text files containing conversation transcripts.
- The app parses each message as `Sender: Message`.
- It detects patterns such as unanswered questions, unclear fee language, pressure phrases, and tone shifts.
- Findings are shown inside the app and can optionally be pushed to a Google Sheet when credentials are configured.

## Running locally

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the app:

```bash
streamlit run app.py
```

3. Open the browser at:

```text
http://localhost:8501
```

## Quick test sample

Use `sample_conversation.txt` to test the app.

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to `https://share.streamlit.io`.
3. Connect your GitHub account and choose this repo.
4. Select `app.py` as the main file.
5. Deploy.

## Deploying to Heroku

1. Install the Heroku CLI and log in.
2. In the project folder, run:

```bash
heroku create
git add .
git commit -m "prepare Streamlit deploy"
git push heroku main
```

3. Open the app with:

```bash
heroku open
```

## Google Sheets integration

Set the `GOOGLE_SHEETS_CREDENTIALS` environment variable to the path of a service account JSON file.
Then provide the target sheet ID in the app.
