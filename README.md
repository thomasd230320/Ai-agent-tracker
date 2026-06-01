# 🛰️ AI Agent Activity Dashboard (Simulation)

Dispatch a task to an autonomous AI agent and **watch it work in real time** —
with **no API key, no account, no billing, and no rate limits**. Everything is
simulated locally, so it runs **free anywhere**, on phone + computer.

| Left — 🎯 Mission Control | Right — 🛰️ Live Agent Activity |
| --- | --- |
| The task you dispatch and the agent's result. | A streaming feed of the agent's narration, the tools it "calls", the arguments, and the result of each step — as it happens. |

This repo ships the dashboard in **two forms** — pick whichever host you like:

| Version | Folder | Tech | Best host |
| --- | --- | --- | --- |
| **Streamlit app** | `app.py` | Python / Streamlit | Streamlit Community Cloud, Render, HF Spaces |
| **Browser app** | `web/` | Static HTML + CSS + JS | **Vercel**, Netlify, GitHub Pages |

Both simulate the same five tools (`execute_web_search`, `fetch_system_metrics`,
`query_database`, `analyze_data`, `send_notification`) and behave identically.

## Run locally

**Streamlit version:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Browser version** (no install needed — it's static):
```bash
# any static server works, e.g.:
python -m http.server -d web 8000
# then open http://localhost:8000
```
…or just open `web/index.html` in your browser.

## Deploy

See [`DEPLOY.md`](DEPLOY.md) for click-by-click steps:
- **Vercel** (or Netlify / GitHub Pages) — deploy the static `web/` folder. No
  key, no build, works on phone + computer.
- **Streamlit Community Cloud** — deploy `app.py`.

> The browser version runs great on **Vercel** because it's 100% client-side
> (no server, no WebSocket). The Streamlit version can't run on Vercel —
> Streamlit needs a persistent server — so use Streamlit Cloud for that one.

## Wiring in a real model later

Everything is simulated today. To connect a real LLM (Claude, Gemini, …), the
agent loop is isolated in one place: `process_task()` in `app.py` (or
`runTask()` in `web/app.js`). Swap the simulated tool calls for real model calls
there — note that a real model needs an API key + billing, which is why this
demo stays fully simulated and free.
