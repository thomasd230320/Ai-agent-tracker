# 🤖 AI Agent Activity Dashboard

Give an agent a task and watch a **little robot work in its room** — it busies
about while working and rests when it's done. Free, no API key, no limits.

## Repo layout

| Path | What it is | Best host |
| --- | --- | --- |
| `index.html`, `styles.css`, `app.js` (**root**) | The **animated robot** dashboard — static HTML/CSS/JS, runs in the browser | **Vercel** / Netlify / GitHub Pages (zero config) |
| `streamlit/app.py` | Same simulation as a Streamlit app | Streamlit Community Cloud |
| `local/claude_agent_app.py` | **Real Claude** version (runs on your Pro/Max subscription, local only) | Run locally — see `local/README.md` |

The static root site is the one with the robot, and it's the easiest to host.

## See it instantly (no hosting)

Download the repo (GitHub → **Code → Download ZIP**), extract it, and
**double‑click `index.html`** — it opens in your browser. Type a task (or hit
**🎲 Random task**) and watch the robot get to work, then rest when finished.

Or serve it locally:
```bash
python -m http.server 8000      # then open http://localhost:8000
```

## Deploy (for phone + computer)

See [`DEPLOY.md`](DEPLOY.md). Short version:
- **Vercel** — import the repo and click **Deploy**. The static site is at the
  repo root, so **no settings are needed** (no Root Directory, no build).
- **Streamlit Cloud** — deploy with main file path `streamlit/app.py`.

> The robot lives in the **root static site** (Vercel/Netlify/Pages). The
> Streamlit version (`streamlit/app.py`) is the plain simulation without the
> robot animation.

## Real Claude (optional, local)

`local/claude_agent_app.py` wires the dashboard to real Claude via the Claude
Agent SDK on your Pro/Max subscription (no API key, no per‑use cost) — but it
runs locally only. Setup in [`local/README.md`](local/README.md).
