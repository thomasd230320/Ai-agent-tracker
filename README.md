# 🧠 AI Agent Thought Dashboard

A single-file [Streamlit](https://streamlit.io) app that visualizes a Claude
agent's reasoning **in real time**. The screen is split into two side-by-side
columns:

| Left — 💬 Chat | Right — 🛰️ Agent Activity |
| --- | --- |
| Your messages and the agent's final answers, as a clean chat. | A live log of the model's *thinking*, the *tools* it calls, the *arguments* it passes, and each call's *execution status* — shown before the final answer. |

Built with the modern **Anthropic Python SDK** and Anthropic **tool calling
(function calling)**, with two mock tools the model can choose to invoke:

- `execute_web_search(query)` — returns canned, plausible search results.
- `fetch_system_metrics()` — returns a randomized live-metrics snapshot.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run app.py
```

If `ANTHROPIC_API_KEY` is missing, the app shows a clear, actionable error
instead of crashing.

## How it works

1. Your message is appended to the conversation and sent to Claude with the two
   tool definitions.
2. The response is **streamed**: extended (adaptive) thinking is rendered live
   in the right column; the answer text streams into the left chat bubble.
3. If Claude returns a `tool_use` block, the right column intercepts it,
   displays the tool name (`st.info`) and arguments (`st.json`), runs the local
   Python function, shows the result/status (`st.success` / `st.error`), and
   feeds the `tool_result` back into the API loop.
4. The loop repeats until Claude stops calling tools, then the final answer is
   shown. Turns that need no tool are handled gracefully ("Answered directly").

State (chat history + activity log) is kept in `st.session_state`, so it
persists across Streamlit reruns. Per-turn token usage (including prompt-cache
hits) is shown in the activity log.

## Model note

The brief asked for `claude-3-5-sonnet`, but that snapshot has been **retired**
by Anthropic and now returns a 404. The app therefore defaults to the current
Sonnet — **`claude-sonnet-4-6`**, the documented drop-in replacement. Change the
single `MODEL` constant at the top of `app.py` to use a different model.

You can toggle the live "agent reasoning" view from the sidebar, and clear the
conversation at any time.
