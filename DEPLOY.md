# Deploying to Streamlit Community Cloud

Streamlit Community Cloud (https://share.streamlit.io) is free and purpose-built
for Streamlit apps. This app runs there with no code changes, and because it uses
a Gemini **API key** (not a subscription) it works on your **phone and computer**
at the same public URL.

## Prerequisites

- The code is on GitHub (it is — repo `thomasd230320/Ai-agent-tracker`).
- A **free** Gemini API key — get one at https://aistudio.google.com → **Get API
  key** (sign in with Google; no card). A Gemini key starts with `AIza...`.
- A Streamlit Community Cloud account (sign in with GitHub).

## Steps

1. Go to https://share.streamlit.io and **sign in with GitHub**.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `thomasd230320/Ai-agent-tracker`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Open **Advanced settings → Secrets** and paste your **real** key:
   ```toml
   GEMINI_API_KEY = "AIza...your-real-key..."
   ```
5. Click **Deploy**. First boot installs `requirements.txt` and starts the app;
   you'll get a public `*.streamlit.app` URL that works on any device.

## Notes

- **Never paste your key into chat, code, or commits.** Put it only in the Cloud
  **Secrets** box. `.streamlit/secrets.toml` is git-ignored; a non-secret
  template lives at `.streamlit/secrets.toml.example`.
- **Secrets** are read as `st.secrets["GEMINI_API_KEY"]` (the app also accepts a
  `GEMINI_API_KEY` / `GOOGLE_API_KEY` environment variable for local runs).
- **Updates:** every push to the deployed branch auto-redeploys.
- **Cost:** the Gemini free tier is rate-limited but **free** — no surprise bills.
- **Sleeping:** free apps sleep after inactivity and wake on the next visit.

## Other hosts

Also runs as-is on Hugging Face Spaces (Streamlit SDK), Render, Railway, and
Fly.io. It will **not** run on Vercel — Streamlit needs a persistent WebSocket
server, which Vercel's serverless functions don't provide.
