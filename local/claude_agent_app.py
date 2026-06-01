"""
AI Agent Activity Dashboard — REAL Claude, local, on your Pro/Max subscription
==============================================================================

This version wires the dashboard to **real Claude** via the Claude Agent SDK,
authenticated by your **Claude Code login** (Pro/Max subscription) — so there is
**no API key and no per-use cost**. You dispatch a task, and you watch the real
agent think, call tools, and work **until it's done**.

  • Left  — 🎯 Mission Control: the task and Claude's final answer.
  • Right — 🛰️ Live Agent Activity: Claude's real reasoning, tool calls, and
            results, streamed as they happen.

⚠️ Runs LOCALLY only (it talks to the Claude Code engine on your machine); it
   is not a hosted/public app. One-time setup is in local/README.md:

     1) Install Node.js, then:  npm install -g @anthropic-ai/claude-code
     2) Log in with your subscription:  claude   (choose your Claude account)
     3) pip install -r local/requirements.txt
     4) streamlit run local/claude_agent_app.py

The agent is restricted to five safe, simulated tools (no access to your files
or shell), so it's contained — but Claude's reasoning and decisions are real.
"""

from __future__ import annotations

import json
import random
from datetime import datetime

import anyio
import streamlit as st
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    query,
    tool,
)

PAGE_TITLE = "AI Agent Activity Dashboard — Real Claude"

EXAMPLE_TASKS = [
    "Check system health and tell me if anything looks unusual",
    "Research the latest in AI agents and summarise it",
    "Pull recent orders from the database and describe the trend",
    "Investigate the error-rate situation and notify the team",
]

SYSTEM_PROMPT = (
    "You are an autonomous AI agent whose work is shown on a live dashboard. "
    "Carry out the user's task step by step.\n\n"
    "Use ONLY these tools (do not attempt to read files, run shell commands, or "
    "use any other tools):\n"
    "  • execute_web_search(query)\n"
    "  • fetch_system_metrics()\n"
    "  • query_database(table)\n"
    "  • analyze_data(subject)\n"
    "  • send_notification(channel, message)\n\n"
    "Briefly say what you're about to do before each tool call. When you have "
    "what you need, give a clear, concise final answer for the user."
)

# --------------------------------------------------------------------------- #
# Simulated tool data (the tools are real tool calls Claude makes; the data
# they return is mock, so nothing touches your real systems)
# --------------------------------------------------------------------------- #


def _web_search(query_str: str) -> str:
    slug = query_str.strip().replace(" ", "-").lower() or "query"
    return json.dumps(
        {
            "query": query_str,
            "result_count": 3,
            "results": [
                {"title": f"{query_str} — Overview", "url": f"https://example.com/{slug}",
                 "snippet": f"A concise overview of '{query_str}' and recent developments."},
                {"title": f"Latest on {query_str}", "url": f"https://news.example.com/?q={slug}",
                 "snippet": f"Recent reporting related to '{query_str}'."},
            ],
        },
        indent=2,
    )


def _metrics() -> str:
    return json.dumps(
        {
            "cpu_percent": round(random.uniform(3, 95), 1),
            "memory_percent": round(random.uniform(28, 93), 1),
            "disk_percent": round(random.uniform(40, 88), 1),
            "error_rate_per_min": round(random.uniform(0, 14), 2),
            "uptime_hours": round(random.uniform(1, 1200), 1),
            "sampled_at": datetime.now().isoformat(timespec="seconds"),
        },
        indent=2,
    )


def _database(table: str) -> str:
    n = random.randint(3, 9)
    return json.dumps(
        {"table": table, "row_count": n,
         "sample": [{"id": 1000 + i, "value": round(random.uniform(10, 999), 2)} for i in range(n)]},
        indent=2,
    )


def _analyze(subject: str) -> str:
    return json.dumps(
        {"subject": subject,
         "insights": random.sample(
             ["trend is rising week over week", "two outliers excluded",
              "correlates with traffic volume", "no anomalies this window"], k=2),
         "confidence": round(random.uniform(0.72, 0.98), 2)},
        indent=2,
    )


def _notify(channel: str, message: str) -> str:
    return json.dumps({"channel": channel, "delivered": True, "message": message}, indent=2)


# --- Agent SDK tool wrappers (in-process MCP server) ----------------------- #


@tool("execute_web_search", "Search the web for current/external information.", {"query": str})
async def t_web_search(args):
    return {"content": [{"type": "text", "text": _web_search(args.get("query", ""))}]}


@tool("fetch_system_metrics", "Fetch live system metrics (CPU, memory, disk, uptime, error rate).", {})
async def t_metrics(args):
    return {"content": [{"type": "text", "text": _metrics()}]}


@tool("query_database", "Query a database table for recent records.", {"table": str})
async def t_database(args):
    return {"content": [{"type": "text", "text": _database(args.get("table", "records"))}]}


@tool("analyze_data", "Analyse gathered data on a subject and return insights.", {"subject": str})
async def t_analyze(args):
    return {"content": [{"type": "text", "text": _analyze(args.get("subject", "the data"))}]}


@tool("send_notification", "Send a status notification to a channel.", {"channel": str, "message": str})
async def t_notify(args):
    return {"content": [{"type": "text", "text": _notify(args.get("channel", "#ops"), args.get("message", ""))}]}


TOOL_SERVER = create_sdk_mcp_server(
    name="tools",
    version="1.0.0",
    tools=[t_web_search, t_metrics, t_database, t_analyze, t_notify],
)

ALLOWED_TOOLS = [f"mcp__tools__{n}" for n in
                 ["execute_web_search", "fetch_system_metrics", "query_database", "analyze_data", "send_notification"]]

# Block built-in tools so the agent stays contained (no real files/shell/web).
DISALLOWED_TOOLS = ["Bash", "Edit", "Write", "Read", "Glob", "Grep", "WebSearch",
                    "WebFetch", "NotebookEdit", "TodoWrite", "KillShell", "Task"]


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"tools": TOOL_SERVER},
        allowed_tools=ALLOWED_TOOLS,
        disallowed_tools=DISALLOWED_TOOLS,
        permission_mode="bypassPermissions",  # auto-run the (safe) custom tools, no prompts
        max_turns=12,
    )


# --------------------------------------------------------------------------- #
# Session state & rendering
# --------------------------------------------------------------------------- #


def init_state() -> None:
    st.session_state.setdefault("chat_log", [])
    st.session_state.setdefault("activity_log", [])


def render_log_entry(entry: dict, c) -> None:
    kind = entry["kind"]
    if kind == "status":
        c.caption(entry["text"])
    elif kind == "thinking":
        with c.expander("🧠 Reasoning", expanded=False):
            st.markdown(entry["text"])
    elif kind == "tool_call":
        c.info(f"🛠️ **Tool call:** `{entry['name']}`")
        if entry.get("input"):
            c.json(entry["input"])
        else:
            c.caption("(no arguments)")
    elif kind == "tool_result":
        if entry.get("is_error"):
            c.error(f"❌ `{entry['name']}` returned an error")
        else:
            c.success(f"✅ `{entry['name']}` completed")
        c.code(entry["output"], language="json")
    elif kind == "error":
        c.error(entry["text"])


def log_event(entry: dict, c) -> None:
    st.session_state.activity_log.append(entry)
    render_log_entry(entry, c)


def _stringify_tool_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", json.dumps(block)))
            else:
                parts.append(getattr(block, "text", str(block)))
        return "\n".join(parts)
    return str(content)


# --------------------------------------------------------------------------- #
# Real agent run (Claude Agent SDK)
# --------------------------------------------------------------------------- #


async def _drive(task: str, handle) -> None:
    async for message in query(prompt=task, options=build_options()):
        handle(message)


def process_turn(task: str, chat_col, log_col) -> None:
    st.session_state.chat_log.append({"role": "user", "text": task})
    with chat_col:
        with st.chat_message("user"):
            st.markdown(task)
        assistant_box = st.chat_message("assistant")
    with assistant_box:
        status_slot = st.empty()
        answer_slot = st.empty()
    status_slot.markdown("🟢 **Claude** is working…")

    turn_log = log_col.container()
    log_event({"kind": "status", "text": f"▶️ Task received · {datetime.now():%H:%M:%S}"}, turn_log)

    state = {"answer": "", "cost": None, "names": {}}

    def handle(message) -> None:
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ThinkingBlock):
                    if block.thinking.strip():
                        log_event({"kind": "thinking", "text": block.thinking.strip()}, turn_log)
                elif isinstance(block, ToolUseBlock):
                    short = block.name.split("__")[-1]
                    state["names"][block.id] = short
                    log_event({"kind": "tool_call", "name": short, "input": block.input or {}}, turn_log)
                elif isinstance(block, TextBlock):
                    if block.text.strip():
                        state["answer"] += (("\n\n" if state["answer"] else "") + block.text.strip())
                        answer_slot.markdown(state["answer"])
        elif isinstance(message, UserMessage):
            for block in (message.content or []):
                if isinstance(block, ToolResultBlock):
                    name = state["names"].get(block.tool_use_id, "tool")
                    log_event(
                        {"kind": "tool_result", "name": name,
                         "output": _stringify_tool_content(block.content),
                         "is_error": bool(block.is_error)},
                        turn_log,
                    )
        elif isinstance(message, ResultMessage):
            state["cost"] = getattr(message, "total_cost_usd", None)
            if not state["answer"] and getattr(message, "result", None):
                state["answer"] = message.result
                answer_slot.markdown(state["answer"])

    try:
        anyio.run(_drive, task, handle)
    except Exception as exc:  # noqa: BLE001
        msg = (
            f"⚠️ Could not reach the Claude agent: {exc}\n\n"
            "Make sure Claude Code is installed and you're logged in:\n"
            "`npm install -g @anthropic-ai/claude-code` then run `claude` and sign "
            "in with your Claude (Pro/Max) account. See local/README.md."
        )
        log_event({"kind": "error", "text": msg}, turn_log)
        status_slot.markdown("🔴 **Stopped.**")
        answer_slot.markdown(state["answer"] or msg)
        st.session_state.chat_log.append({"role": "assistant", "text": state["answer"] or msg})
        return

    answer = state["answer"] or "_(The agent finished without a final message.)_"
    status_slot.markdown("✅ **Claude** finished.")
    answer_slot.markdown(answer)
    cost = state.get("cost")
    extra = f" · 💲{cost:.4f}" if isinstance(cost, (int, float)) and cost else " · billed to your subscription"
    log_event({"kind": "status", "text": f"🏁 Done{extra}"}, turn_log)
    st.session_state.chat_log.append({"role": "assistant", "text": answer})


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🛰️", layout="wide")
    init_state()

    with st.sidebar:
        st.header("⚙️ Controls")
        st.success("Real Claude · your Pro/Max subscription · no API key")
        st.caption("Runs locally via the Claude Agent SDK (Claude Code login).")
        st.divider()
        queued = None
        if st.button("🎲 Dispatch a random task", use_container_width=True):
            queued = random.choice(EXAMPLE_TASKS)
        st.subheader("Example tasks")
        st.markdown("\n".join(f"- *{t}*" for t in EXAMPLE_TASKS))
        st.divider()
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_log = []
            st.session_state.activity_log = []
            st.rerun()

    st.title(f"🛰️ {PAGE_TITLE}")
    st.caption(
        "Dispatch a task and watch **real Claude** work until it's done.  "
        "Left: the task & final answer.  Right: live reasoning, tool calls, and results."
    )

    typed = st.chat_input("Give Claude a task…")
    task = typed or queued

    chat_col, log_col = st.columns(2, gap="large")

    with chat_col:
        st.subheader("🎯 Mission Control")
        if not st.session_state.chat_log and not task:
            st.info("Give Claude a task (type below or use the sidebar). Its live "
                    "reasoning and tool calls appear on the right.")
        for message in st.session_state.chat_log:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])

    with log_col:
        st.subheader("🛰️ Live Agent Activity")
        if not st.session_state.activity_log and not task:
            st.caption("No activity yet.")
    for entry in st.session_state.activity_log:
        render_log_entry(entry, log_col)

    if task:
        process_turn(task, chat_col, log_col)


if __name__ == "__main__":
    main()
