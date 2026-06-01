# 🛰️ AI Agent Activity Dashboard

A single-file [Streamlit](https://streamlit.io) app that lets you launch an AI
agent and **watch it work in real time**. The screen is split into two
side-by-side columns:

| Left — 🎯 Tasks & Results | Right — 🛰️ Live Agent Activity |
| --- | --- |
| The task you give the agent and its final answer. | A streaming feed of what the agent is doing — its narration, the tools it calls, the arguments it passes, and the status of each call — as it happens. |

Powered by **Google Gemini** (the **free** tier from
[aistudio.google.com](https://aistudio.google.com)) with function calling
(tools) and streaming. Two mock tools the agent can choose to call:

- `execute_web_search(query)` — returns canned, plausible search results.
- `fetch_system_metrics()` — returns a randomized live-metrics snapshot.

## Quick start

```bash
pip install -r requirements.txt
# Get a free key at https://aistudio.google.com → "Get API key"
export GEMINI_API_KEY="AIza..."
streamlit run app.py
```

If no key is found, the app shows a clear, actionable error instead of crashing.

## Why Gemini?

The free Gemini tier means **no pay-as-you-go billing** — and because it's a
normal API key (not a subscription), the app **can be hosted** on Streamlit
Community Cloud, so it works on your **phone and computer** at the same URL.

## How it works

1. You give the agent a **task**.
2. Gemini is called with the task and the two tool definitions, and the response
   is **streamed**: the agent's narration shows live in the right column.
3. If Gemini returns a function call, the right column shows the tool name
   (`st.info`) and arguments (`st.json`), runs the local Python function, shows
   the result/status (`st.success` / `st.error`), and feeds the result back into
   the loop.
4. The agent keeps going **autonomously** (up to `MAX_STEPS`) until it stops
   calling tools, then the final answer appears on the left. Tasks needing no
   tool are handled gracefully ("Answered directly").

State (task history + activity log) is kept in `st.session_state`, so it persists
across Streamlit reruns. Per-turn token usage is shown in the activity log.

## Deploying

See [`DEPLOY.md`](DEPLOY.md) for click-by-click Streamlit Community Cloud steps.
The app also runs on Hugging Face Spaces, Render, Railway, and Fly.io. It will
**not** run on Vercel — Streamlit needs a persistent WebSocket server, which
Vercel's serverless functions don't provide.

## Model note

Defaults to **`gemini-2.0-flash`** (reliable on the free tier). Change the single
`MODEL` constant at the top of `app.py` to use `gemini-2.5-flash` (adds visible
reasoning) or another model.
