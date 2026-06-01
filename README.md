# 🛰️ AI Agent Activity Dashboard (Simulation)

A single-file [Streamlit](https://streamlit.io) app that lets you dispatch a
task to an autonomous AI agent and **watch it work in real time** — with **no
API key, no account, no billing, and no rate limits**. Everything is simulated
locally, so it runs **free anywhere** (and on your phone + computer once hosted).

| Left — 🎯 Mission Control | Right — 🛰️ Live Agent Activity |
| --- | --- |
| The task you dispatch and the agent's result. | A streaming feed of the agent's narration, the tools it "calls", the arguments, and the result of each step — as it happens. |

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it — no key, no secrets, no setup. It just runs.

## What it does

- Dispatch a task (type your own, or hit **🎲 Dispatch a random task**).
- A named agent is assigned and **autonomously** plans which tools to use based
  on the task, then streams each step live into the activity feed:
  - 💭 narration of what it's about to do,
  - 🛠️ the tool call + arguments (`st.info` / `st.json`),
  - ✅ the tool result (`st.success` / `st.code`),
- …and finishes with a summarised result on the left.

Five simulated tools drive the activity: `execute_web_search`,
`fetch_system_metrics`, `query_database`, `analyze_data`, and
`send_notification`. All return realistic mock data — **nothing leaves your
machine and there's nothing to pay for.**

State (task history + activity log) lives in `st.session_state`, so it persists
across Streamlit reruns.

## Deploying

See [`DEPLOY.md`](DEPLOY.md) for click-by-click Streamlit Community Cloud steps.
Because it needs no API key, deployment is just: pick the repo, set the main file
to `app.py`, and click Deploy — it works on phone + computer at one URL.

> Want to wire it to a *real* LLM later (Claude, Gemini, etc.)? The agent loop in
> `process_task()` is the single place to swap the simulated tool calls for real
> model calls.
