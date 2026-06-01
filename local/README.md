# Real Claude dashboard (local, on your Pro/Max subscription)

`claude_agent_app.py` wires the dashboard to **real Claude** via the
[Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview),
authenticated by your **Claude Code login** — so there's **no API key and no
per-use cost** (it draws on your Claude Pro/Max subscription).

You dispatch a task and watch the real agent **think → call tools → work until
done**, live.

> ⚠️ **This one runs locally only.** It talks to the Claude Code engine on your
> machine, so it can't be a hosted/phone URL like the free simulation. Your
> hosted simulation (`app.py` / `web/`) is unaffected.

## One-time setup

1. **Install Node.js** (v18+): https://nodejs.org
2. **Install the Claude Code CLI:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
3. **Log in with your Claude subscription:**
   ```bash
   claude
   ```
   When prompted, choose to log in with your **Claude account** (Pro/Max) — a
   browser window opens for sign-in. (Tip: make sure the `ANTHROPIC_API_KEY`
   environment variable is **not** set, so it uses your subscription and not a
   paid API key.)
4. **Install the Python deps:**
   ```bash
   pip install -r local/requirements.txt
   ```

## Run it

```bash
streamlit run local/claude_agent_app.py
```

Open the local URL it prints, type a task (or use **🎲 Dispatch a random task**),
and watch Claude work in the right-hand activity feed until it's done.

## Notes

- **Cost:** none beyond your Claude subscription — no API key, no pay-as-you-go.
- **Safety / scope:** the agent is restricted to five **simulated** tools
  (`execute_web_search`, `fetch_system_metrics`, `query_database`,
  `analyze_data`, `send_notification`) and is blocked from your files and shell.
  Claude's *reasoning and decisions* are real; the tool *data* is mock, so it's
  a contained demo. To let it do real work on your machine, you'd swap the
  custom tools for the SDK's built-in tools in `build_options()` — do that only
  if you understand the implications.
- **Why local-only:** a personal subscription can't power a hosted/public
  service. For an "on phone + computer" version, use the free simulation
  (`app.py` on Streamlit Cloud, or `web/` on Vercel).
