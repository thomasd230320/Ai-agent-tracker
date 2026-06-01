# Deploying to Streamlit Community Cloud

Streamlit Community Cloud (https://share.streamlit.io) is free and purpose-built
for Streamlit apps. This app needs **no API key and no secrets**, so deployment
is as simple as it gets — and it works on your **phone and computer** at one URL.

## Steps

1. Go to https://share.streamlit.io and **sign in with GitHub**.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `thomasd230320/Ai-agent-tracker`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy**. First boot installs `requirements.txt` (just Streamlit) and
   starts the app; you'll get a public `*.streamlit.app` URL.

**No Secrets step needed** — there's no key to configure. If you previously set
an `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` secret, you can delete it; the
simulation ignores them.

## Notes

- **Cost:** $0. The app makes no external API calls, so there are no usage caps
  or bills — ever.
- **Updates:** every push to `main` auto-redeploys.
- **Sleeping:** free apps sleep after inactivity and wake on the next visit.

## Other hosts

Also runs as-is on Hugging Face Spaces (Streamlit SDK), Render, Railway, and
Fly.io. It will **not** run on Vercel — Streamlit needs a persistent WebSocket
server, which Vercel's serverless functions don't provide.
