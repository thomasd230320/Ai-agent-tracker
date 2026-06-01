# Deploying to Streamlit Community Cloud

Streamlit Community Cloud (https://share.streamlit.io) is free and purpose-built
for Streamlit apps. This app runs there with no code changes.

## Prerequisites

- The code is on GitHub (it is — repo `thomasd230320/Ai-agent-tracker`).
- An Anthropic API key (`sk-ant-...`).
- A Streamlit Community Cloud account (sign in with GitHub).

## Steps

1. Go to https://share.streamlit.io and **sign in with GitHub**, authorizing
   access to the repository.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `thomasd230320/Ai-agent-tracker`
   - **Branch:** `main` (merge the PR first), or the feature branch
     `claude/nifty-ramanujan-Z9dBt` to deploy before merging.
   - **Main file path:** `app.py`
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy**. First boot installs `requirements.txt` and starts the app;
   you'll get a public `*.streamlit.app` URL.

## Notes

- **Dependencies:** taken from `requirements.txt` automatically.
- **Secrets:** the app reads the key from `st.secrets` first, then the
  `ANTHROPIC_API_KEY` environment variable, so the secret above is all you need.
  You can edit secrets later via the app's **⋮ menu → Settings → Secrets**
  (the app reboots on save).
- **Updates:** every push to the deployed branch auto-redeploys.
- **Sleeping:** free apps sleep after inactivity and wake on the next visit.
- **Don't commit real keys.** `.streamlit/secrets.toml` is git-ignored; use the
  Cloud Secrets UI (or copy `.streamlit/secrets.toml.example` locally).

## Other hosts

This app also runs as-is on Hugging Face Spaces (Streamlit SDK), Render,
Railway, and Fly.io. It will **not** run on Vercel — Streamlit needs a
persistent WebSocket server, which Vercel's serverless functions don't provide.
