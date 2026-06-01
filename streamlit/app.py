"""
AI Agent Activity Dashboard  (Simulation — no API key, free forever)
====================================================================

A single-file Streamlit app that lets you dispatch a task to an autonomous AI
agent and **watch it work in real time** — with no external API, no key, no
billing, and no rate limits. Everything is simulated locally, so it runs free
anywhere (and on your phone + computer once hosted).

  • Left  — 🎯 Mission Control: the task you dispatch and the agent's result.
  • Right — 🛰️ Live Agent Activity: a streaming feed of what the agent is doing —
            its narration, the tools it "calls", the arguments, and the result
            of each step — as it happens.

Run it:

    pip install -r requirements.txt          # just streamlit
    streamlit run app.py
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime

import streamlit as st

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PAGE_TITLE = "AI Agent Activity Dashboard"

# Named agents — one is assigned to each dispatched task.
AGENTS = ["Atlas", "Nova", "Orion", "Sentinel", "Echo"]

EXAMPLE_TASKS = [
    "Check system health and flag anything unusual",
    "Research the latest in AI agents and summarise it",
    "Pull recent orders from the database and analyse the trend",
    "Investigate the spike in error rates and notify the team",
    "Find the top competitors for our product and compare them",
    "Audit current resource usage across the servers",
]

# Streaming speed (seconds). Small = snappy but still visibly "live".
WORD_DELAY = 0.015
STEP_PAUSE = 0.35

# --------------------------------------------------------------------------- #
# Simulated tools — each returns a JSON string, just like a real tool result
# --------------------------------------------------------------------------- #


def tool_execute_web_search(query: str) -> str:
    slug = query.strip().replace(" ", "-").lower() or "query"
    results = [
        {
            "title": f"{query.title()} — Overview",
            "url": f"https://example.com/{slug}",
            "snippet": f"A concise overview of '{query}' and recent developments.",
        },
        {
            "title": f"Latest on {query.title()}",
            "url": f"https://news.example.com/search?q={query.replace(' ', '+')}",
            "snippet": f"Recent reporting related to '{query}', updated {datetime.now():%B %Y}.",
        },
        {
            "title": f"{query.title()} explained",
            "url": f"https://wiki.example.com/wiki/{query.replace(' ', '_')}",
            "snippet": "Background, context, and frequently asked questions.",
        },
    ]
    return json.dumps({"query": query, "result_count": len(results), "results": results}, indent=2)


def tool_fetch_system_metrics() -> str:
    return json.dumps(
        {
            "cpu_percent": round(random.uniform(3.0, 95.0), 1),
            "memory_percent": round(random.uniform(28.0, 93.0), 1),
            "disk_percent": round(random.uniform(40.0, 88.0), 1),
            "active_connections": random.randint(12, 480),
            "error_rate_per_min": round(random.uniform(0.0, 14.0), 2),
            "uptime_hours": round(random.uniform(1.0, 1200.0), 1),
            "sampled_at": datetime.now().isoformat(timespec="seconds"),
        },
        indent=2,
    )


def tool_query_database(table: str) -> str:
    n = random.randint(3, 9)
    rows = [
        {"id": 1000 + i, "name": random.choice(["Alice", "Bob", "Chen", "Dara", "Esa"]),
         "value": round(random.uniform(10, 999), 2)}
        for i in range(n)
    ]
    return json.dumps({"table": table, "row_count": n, "sample": rows}, indent=2)


def tool_analyze_data(subject: str) -> str:
    return json.dumps(
        {
            "subject": subject,
            "insights": random.sample(
                [
                    "trend is rising week over week",
                    "two outliers detected and excluded",
                    "strong correlation with traffic volume",
                    "no anomalies in the latest window",
                    "seasonality accounts for most variance",
                ],
                k=2,
            ),
            "confidence": round(random.uniform(0.72, 0.98), 2),
        },
        indent=2,
    )


def tool_send_notification(channel: str, message: str) -> str:
    return json.dumps(
        {"channel": channel, "delivered": True, "message": message, "at": datetime.now().isoformat(timespec="seconds")},
        indent=2,
    )


def run_sim_tool(name: str, args: dict) -> str:
    if name == "execute_web_search":
        return tool_execute_web_search(args.get("query", ""))
    if name == "fetch_system_metrics":
        return tool_fetch_system_metrics()
    if name == "query_database":
        return tool_query_database(args.get("table", "records"))
    if name == "analyze_data":
        return tool_analyze_data(args.get("subject", "the data"))
    if name == "send_notification":
        return tool_send_notification(args.get("channel", "#ops"), args.get("message", ""))
    return json.dumps({"error": f"unknown tool '{name}'"})


# --------------------------------------------------------------------------- #
# The "brain": decide which tools to use for a task (keyword-driven, simulated)
# --------------------------------------------------------------------------- #


def _derive_query(task: str) -> str:
    words = [w for w in task.split() if w.lower() not in
             {"the", "a", "an", "for", "and", "to", "our", "of", "on", "in", "find", "research"}]
    return " ".join(words[:6]) or task


def plan_tools(task: str) -> list[tuple[str, dict]]:
    """Pick a realistic sequence of (tool, args) for the task."""
    t = task.lower()
    plan: list[tuple[str, dict]] = []

    if any(k in t for k in ["metric", "health", "cpu", "memory", "server", "performance", "load", "uptime", "resource", "error rate"]):
        plan.append(("fetch_system_metrics", {}))
    if any(k in t for k in ["search", "latest", "news", "find", "research", "web", "competitor", "compare", "look up"]):
        plan.append(("execute_web_search", {"query": _derive_query(task)}))
    if any(k in t for k in ["database", "db", "users", "records", "rows", "table", "orders", "customers", "data"]):
        plan.append(("query_database", {"table": random.choice(["orders", "users", "events", "metrics"])}))

    if not plan:  # default plan
        plan.append(("execute_web_search", {"query": _derive_query(task)}))

    if random.random() < 0.75:  # agents usually analyse what they gathered
        plan.append(("analyze_data", {"subject": _derive_query(task)}))
    if any(k in t for k in ["notify", "alert", "email", "message", "slack", "ping", "team", "investigate"]):
        plan.append(("send_notification", {"channel": "#ops", "message": f"Update on: {_derive_query(task)}"}))

    return plan[:4]


def narration_for(agent: str, name: str, args: dict) -> str:
    return {
        "fetch_system_metrics": "Checking live system metrics to assess current health.",
        "execute_web_search": f"Searching the web for \"{args.get('query', '')}\" to gather context.",
        "query_database": f"Querying the `{args.get('table', 'records')}` table for relevant records.",
        "analyze_data": f"Analysing the gathered data on \"{args.get('subject', 'the topic')}\".",
        "send_notification": f"Sending a status update to {args.get('channel', '#ops')}.",
    }.get(name, "Working on the next step.")


def compose_answer(agent: str, findings: list[tuple[str, str]]) -> str:
    parts = []
    for name, out in findings:
        try:
            d = json.loads(out)
        except Exception:  # noqa: BLE001
            continue
        if name == "fetch_system_metrics":
            hot = d["cpu_percent"] > 80 or d["memory_percent"] > 85 or d["error_rate_per_min"] > 8
            parts.append(
                f"system health looks {'⚠️ elevated' if hot else '✅ healthy'} "
                f"(CPU {d['cpu_percent']}%, memory {d['memory_percent']}%, "
                f"errors {d['error_rate_per_min']}/min)"
            )
        elif name == "execute_web_search":
            parts.append(f"found {d['result_count']} relevant sources on \"{d['query']}\"")
        elif name == "query_database":
            parts.append(f"retrieved {d['row_count']} rows from `{d['table']}`")
        elif name == "analyze_data":
            parts.append(f"analysed the data ({int(d['confidence'] * 100)}% confidence: {d['insights'][0]})")
        elif name == "send_notification":
            parts.append(f"notified the team in {d['channel']}")
    if not parts:
        return f"**{agent}** finished, but had nothing notable to report."
    body = "; ".join(parts)
    return f"**Task complete.** {agent} {body}. Let me know if you'd like a deeper dive."


# --------------------------------------------------------------------------- #
# Session state & rendering
# --------------------------------------------------------------------------- #


def init_state() -> None:
    st.session_state.setdefault("chat_log", [])      # left column
    st.session_state.setdefault("activity_log", [])  # right column


def render_log_entry(entry: dict, c) -> None:
    kind = entry["kind"]
    if kind == "status":
        c.caption(entry["text"])
    elif kind == "narration":
        c.markdown(f"💭 _{entry['text']}_")
    elif kind == "tool_call":
        c.info(f"🛠️ **Tool call:** `{entry['name']}`")
        if entry.get("input"):
            c.json(entry["input"])
        else:
            c.caption("(no arguments)")
    elif kind == "tool_result":
        c.success(f"✅ `{entry['name']}` completed")
        c.code(entry["output"], language="json")


def log_event(entry: dict, c) -> None:
    st.session_state.activity_log.append(entry)
    render_log_entry(entry, c)


def stream_words(slot, prefix: str, text: str) -> None:
    """Type ``text`` into ``slot`` word by word for a live feel."""
    acc = ""
    for word in text.split(" "):
        acc += word + " "
        slot.markdown(prefix + acc)
        time.sleep(WORD_DELAY)
    slot.markdown(prefix + text)


# --------------------------------------------------------------------------- #
# Simulated agent run
# --------------------------------------------------------------------------- #


def process_task(task: str, chat_col, log_col) -> None:
    agent = random.choice(AGENTS)
    st.session_state.chat_log.append({"role": "user", "text": f"**Task:** {task}"})

    with chat_col:
        with st.chat_message("user"):
            st.markdown(f"**Task:** {task}")
        assistant_box = st.chat_message("assistant")
    with assistant_box:
        status_slot = st.empty()
        answer_slot = st.empty()
    status_slot.markdown(f"🟢 **Agent {agent}** is on it…")

    turn_log = log_col.container()
    log_event(
        {"kind": "status", "text": f"▶️ {agent} assigned · {datetime.now():%H:%M:%S}"},
        turn_log,
    )

    plan = plan_tools(task)
    findings: list[tuple[str, str]] = []

    for name, args in plan:
        narration = narration_for(agent, name, args)
        narration_slot = turn_log.empty()
        stream_words(narration_slot, "💭 ", narration)
        st.session_state.activity_log.append({"kind": "narration", "text": narration})

        log_event({"kind": "tool_call", "name": name, "input": args}, turn_log)
        time.sleep(STEP_PAUSE)

        output = run_sim_tool(name, args)
        log_event(
            {"kind": "tool_result", "name": name, "output": output, "is_error": False},
            turn_log,
        )
        findings.append((name, output))
        time.sleep(STEP_PAUSE)

    answer = compose_answer(agent, findings)
    status_slot.markdown(f"✅ **Agent {agent}** finished.")
    stream_words(answer_slot, "", answer)
    st.session_state.chat_log.append({"role": "assistant", "text": answer})
    log_event(
        {"kind": "status", "text": f"🏁 {agent} completed {len(plan)} step(s)."},
        turn_log,
    )


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🛰️", layout="wide")
    init_state()

    # --- Sidebar ---------------------------------------------------------- #
    with st.sidebar:
        st.header("⚙️ Controls")
        st.success("Simulation mode — no API key, no limits, free.")
        st.caption("**Agents on duty**")
        st.markdown("  ·  ".join(f"🤖 {a}" for a in AGENTS))
        st.divider()
        queued = None
        if st.button("🎲 Dispatch a random task", use_container_width=True):
            queued = random.choice(EXAMPLE_TASKS)
        st.caption("Or type your own task at the bottom.")
        st.divider()
        st.subheader("Example tasks")
        st.markdown("\n".join(f"- *{t}*" for t in EXAMPLE_TASKS[:4]))
        st.divider()
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_log = []
            st.session_state.activity_log = []
            st.rerun()

    # --- Header ----------------------------------------------------------- #
    st.title(f"🛰️ {PAGE_TITLE}")
    st.caption(
        "Dispatch a task and watch an autonomous agent work — live.  "
        "Left: the task and result.  Right: the agent's reasoning, tool calls, "
        "and status.  _Simulation: no API key, no cost, no limits._"
    )

    typed = st.chat_input("Dispatch a task to an agent…")
    task = typed or queued

    chat_col, log_col = st.columns(2, gap="large")

    with chat_col:
        st.subheader("🎯 Mission Control")
        if not st.session_state.chat_log and not task:
            st.info(
                "Dispatch a task (type below, or use **🎲 Dispatch a random task** "
                "in the sidebar). The agent's live activity appears on the right."
            )
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
        process_task(task, chat_col, log_col)


if __name__ == "__main__":
    main()
