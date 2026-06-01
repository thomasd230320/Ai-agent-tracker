# Deploying the dashboard

Two versions, two easy hosts. Neither needs an API key or any secrets.

---

## Option A — Browser version on Vercel  (recommended for phone + computer)

The `web/` folder is a plain static site (HTML + CSS + JS) that runs entirely in
the browser, so Vercel can host it perfectly — free, fast, on every device.

1. Push this repo to GitHub (already done: `thomasd230320/Ai-agent-tracker`).
2. Go to https://vercel.com → **Add New… → Project** → **Import** this repo.
3. In the configure screen:
   - **Root Directory:** click **Edit** and set it to **`web`**.
   - **Framework Preset:** **Other**.
   - **Build Command:** leave empty. **Output Directory:** leave default.
   - No Environment Variables needed.
4. Click **Deploy**. You'll get a public `*.vercel.app` URL that works on your
   phone and computer.

> Why `Root Directory = web`? It points Vercel at the static site and keeps it
> from trying to build the Python (`app.py`) file at the repo root.

**Netlify / GitHub Pages** work the same way — serve the `web/` folder as a
static site (set the publish/base directory to `web`).

---

## Option B — Streamlit version on Streamlit Community Cloud

The `app.py` version needs a persistent server, so host it on Streamlit Cloud
(it will **not** run on Vercel).

1. Go to https://share.streamlit.io and **sign in with GitHub**.
2. **Create app → Deploy a public app from GitHub**.
3. **Repository:** `thomasd230320/Ai-agent-tracker` · **Branch:** `main` ·
   **Main file path:** `app.py`.
4. Click **Deploy**. No Secrets step — there's no key to configure.

---

## Notes

- **Cost:** $0 for both. No external API calls, so no usage caps or bills — ever.
- **Updates:** pushing to `main` auto-redeploys on both Vercel and Streamlit Cloud.
- If you previously set an `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` secret on the
  Streamlit app, you can delete it — the simulation ignores it.
