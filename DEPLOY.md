# Deploying the dashboard

The animated robot dashboard is a **static site at the repo root**
(`index.html`, `styles.css`, `app.js`) — no API key, no build, no secrets.

---

## Option A — Vercel  (recommended; phone + computer)

Because the static site is at the **root**, Vercel needs **no special settings**.

1. Push to GitHub (already done: `thomasd230320/Ai-agent-tracker`).
2. https://vercel.com → **Add New… → Project → Import** this repo.
3. Leave everything at the **defaults**:
   - Framework Preset: **Other** (auto-detected).
   - Root Directory: **`./`** (the repo root — leave as is).
   - Build Command / Output Directory: **leave empty/default**.
4. Click **Deploy** → you get a public `*.vercel.app` URL.

> Already created a Vercel project that failed with *"Found app.py…"*? That was
> because the Python file used to be at the root. It's now moved to
> `streamlit/`, so just **redeploy** (Deployments → ⋯ → Redeploy) — or, to be
> safe, delete the old project and re-import fresh with the defaults above.
> A `.vercelignore` also keeps the Python folders out of the Vercel build.

**Netlify / GitHub Pages** work the same way — serve the repo root as a static
site (no build).

---

## Option B — Streamlit Community Cloud

1. https://share.streamlit.io → **sign in with GitHub**.
2. **Create app → Deploy a public app from GitHub**.
3. **Repository:** `thomasd230320/Ai-agent-tracker` · **Branch:** `main` ·
   **Main file path:** `streamlit/app.py`  ← note the `streamlit/` prefix.
4. **Deploy.** No Secrets needed.

> If you have an existing Streamlit Cloud app pointed at `app.py`, update its
> **Main file path** to `streamlit/app.py` (Manage app → Settings), since the
> file moved. (This version has no robot animation — that's the root static site.)

---

## Notes

- **Cost:** $0 for both — no external API calls, no caps, no bills.
- **Updates:** pushing to `main` auto-redeploys on both Vercel and Streamlit Cloud.
- **Real Claude (local):** see `local/README.md` — runs on your Pro/Max
  subscription, locally only.
