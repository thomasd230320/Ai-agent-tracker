"""
AI Agent Thought Dashboard
==========================

A single-file Streamlit application that visualizes a Claude agent's reasoning
in real time. The interface is split into two side-by-side columns:

  • Left  — a clean chat interface (your messages + the agent's final answers).
  • Right — a live "Agent Activity" log that shows the model's thinking, the
            tools it decides to call, the arguments it passes, and the
            execution status of each call, *before* the final answer is shown.

It uses the modern Anthropic Python SDK with tool calling (function calling)
and two mock tools — ``execute_web_search`` and ``fetch_system_metrics``.

Run it:

    pip install -r requirements.txt        # streamlit + anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."  # your Anthropic API key
    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime

import anthropic
import streamlit as st

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# The original request named "claude-3-5-sonnet". That snapshot has been retired
# by Anthropic (it now returns a 404), so we default to the current Sonnet —
# Claude Sonnet 4.6 — which is the documented drop-in replacement. Change this
# single constant if you have access to (or prefer) a different model.
MODEL = "claude-sonnet-4-6"

# We stream every request, so a generous output ceiling is safe. ``max_tokens``
# is only a cap — the model stops as soon as it is done, so a higher value adds
# no latency for short answers, it just prevents truncation on longer ones.
MAX_TOKENS = 8192

PAGE_TITLE = "AI Agent Thought Dashboard"

SYSTEM_PROMPT = (
    "You are an autonomous AI agent running inside a real-time 'Thought "
    "Dashboard'. Reason about each request and decide whether one of your tools "
    "would genuinely help before answering.\n\n"
    "Tools available to you:\n"
    "  • execute_web_search(query) — look up current or external information.\n"
    "  • fetch_system_metrics()    — read live host metrics (CPU, memory, etc.).\n\n"
    "Call a tool only when it actually helps answer the question; if you can "
    "answer directly from your own knowledge, do so. Once you have what you "
    "need, reply with a clear, concise final answer for the user."
)

# Sending the system prompt as a cache-controlled block lets the API reuse this
# (and the tool definitions) as a cached prefix across the multiple round-trips
# of a single tool-using turn, and across turns. See response usage in the
# activity log for cache hits.
SYSTEM_PROMPT_BLOCKS = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
]

# --------------------------------------------------------------------------- #
# Tool definitions (sent to Claude) and their local mock implementations
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "name": "execute_web_search",
        "description": (
            "Search the web for up-to-date information. Call this when the user "
            "asks about current events, recent facts, prices, libraries, or "
            "anything that benefits from fresh external data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to run.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_system_metrics",
        "description": (
            "Fetch a snapshot of live system metrics (CPU, memory, disk, "
            "network, uptime). Call this when the user asks about system health, "
            "performance, load, or resource usage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def execute_web_search(query: str) -> str:
    """Mock web search. Returns plausible canned results as a JSON string."""
    slug = query.strip().replace(" ", "-").lower() or "query"
    results = [
        {
            "title": f"{query.title()} — Overview",
            "url": f"https://example.com/{slug}",
            "snippet": (
                f"A concise overview of '{query}', covering the key facts and "
                "the most relevant recent developments."
            ),
        },
        {
            "title": f"Latest on {query.title()}",
            "url": f"https://news.example.com/search?q={query.replace(' ', '+')}",
            "snippet": (
                f"Recent reporting and analysis related to '{query}', "
                f"updated {datetime.now():%B %Y}."
            ),
        },
        {
            "title": f"{query.title()} explained",
            "url": f"https://wiki.example.com/wiki/{query.replace(' ', '_')}",
            "snippet": "Background, context, and frequently asked questions.",
        },
    ]
    return json.dumps(
        {"query": query, "result_count": len(results), "results": results},
        indent=2,
    )


def fetch_system_metrics() -> str:
    """Mock system metrics. Returns a randomized-but-plausible JSON snapshot."""
    metrics = {
        "cpu_percent": round(random.uniform(3.0, 87.0), 1),
        "memory_percent": round(random.uniform(28.0, 91.0), 1),
        "disk_percent": round(random.uniform(40.0, 78.0), 1),
        "network_mbps": round(random.uniform(0.5, 940.0), 1),
        "active_connections": random.randint(12, 480),
        "load_average": [round(random.uniform(0.1, 4.0), 2) for _ in range(3)],
        "uptime_hours": round(random.uniform(1.0, 1200.0), 1),
        "sampled_at": datetime.now().isoformat(timespec="seconds"),
    }
    return json.dumps(metrics, indent=2)


# Maps a tool name to a callable that accepts the parsed input dict.
TOOL_DISPATCH = {
    "execute_web_search": lambda payload: execute_web_search(payload["query"]),
    "fetch_system_metrics": lambda payload: fetch_system_metrics(),
}


def run_tool(name: str, payload: dict) -> tuple[str, bool]:
    """Execute a tool by name. Returns ``(output_string, is_error)``."""
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return f"Error: unknown tool '{name}'.", True
    try:
        return handler(payload), False
    except Exception as exc:  # noqa: BLE001 - surface any failure back to Claude
        return f"Error while executing '{name}': {exc}", True


# --------------------------------------------------------------------------- #
# Session state & client
# --------------------------------------------------------------------------- #


def init_state() -> None:
    """Initialise the persistent state used across Streamlit reruns."""
    # Raw Anthropic conversation history (the source of truth for the model).
    st.session_state.setdefault("api_messages", [])
    # Left column: list of {"role": ..., "text": ...} for the chat transcript.
    st.session_state.setdefault("chat_log", [])
    # Right column: list of structured activity entries (thinking, tools, ...).
    st.session_state.setdefault("activity_log", [])


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> anthropic.Anthropic:
    """Create (and cache) the Anthropic client for the given key."""
    return anthropic.Anthropic(api_key=api_key)


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #


def render_log_entry(entry: dict, c) -> None:
    """Render a single activity-log entry into container ``c``."""
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
        if entry["is_error"]:
            c.error(f"❌ `{entry['name']}` returned an error")
        else:
            c.success(f"✅ `{entry['name']}` completed")
        c.code(entry["output"], language="json")

    elif kind == "usage":
        bits = [f"in {entry['input']}", f"out {entry['output']}"]
        if entry.get("cache_read"):
            bits.append(f"cache-read {entry['cache_read']}")
        if entry.get("cache_write"):
            bits.append(f"cache-write {entry['cache_write']}")
        c.caption("📊 tokens — " + " · ".join(bits))

    elif kind == "error":
        c.error(entry["text"])


def log_event(entry: dict, c) -> None:
    """Persist an activity entry for future reruns *and* render it live now."""
    st.session_state.activity_log.append(entry)
    render_log_entry(entry, c)


# --------------------------------------------------------------------------- #
# Core agent loop
# --------------------------------------------------------------------------- #


def process_turn(client, prompt: str, chat_col, log_col, show_thinking: bool) -> None:
    """Run the full agentic loop for one user message.

    Streams the model's thinking and tool activity into ``log_col`` and the
    final answer into ``chat_col``, feeding ``tool_result`` blocks back to the
    API until the model stops requesting tools.
    """
    # Record + display the user's message.
    st.session_state.chat_log.append({"role": "user", "text": prompt})
    st.session_state.api_messages.append({"role": "user", "content": prompt})

    with chat_col:
        with st.chat_message("user"):
            st.markdown(prompt)
        assistant_box = st.chat_message("assistant")
    with assistant_box:
        answer_slot = st.empty()
    answer_slot.markdown("_Thinking…_")

    turn_log = log_col.container()
    log_event(
        {"kind": "status", "text": f"▶️ New request · {datetime.now():%H:%M:%S}"},
        turn_log,
    )

    answer_text = ""
    tool_calls_made = 0
    final_stop_reason = "end_turn"
    tok_in = tok_out = tok_cache_read = tok_cache_write = 0

    request_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT_BLOCKS,
        tools=TOOLS,
        messages=st.session_state.api_messages,  # same list object, mutated below
    )
    if show_thinking:
        request_kwargs["thinking"] = {"type": "adaptive"}

    try:
        while True:
            thinking_slot = turn_log.empty() if show_thinking else None
            thinking_buf = ""

            with client.messages.stream(**request_kwargs) as stream:
                for event in stream:
                    if event.type != "content_block_delta":
                        continue
                    delta = event.delta
                    if delta.type == "thinking_delta" and thinking_slot is not None:
                        thinking_buf += delta.thinking
                        thinking_slot.markdown("🧠 **Reasoning…**\n\n" + thinking_buf)
                    elif delta.type == "text_delta":
                        answer_text += delta.text
                        answer_slot.markdown(answer_text)
                response = stream.get_final_message()

            # Persist the round's thinking so history re-renders it as an expander.
            if thinking_buf.strip():
                st.session_state.activity_log.append(
                    {"kind": "thinking", "text": thinking_buf}
                )
            elif thinking_slot is not None:
                thinking_slot.empty()

            # Keep the full assistant turn (thinking + tool_use + text, with
            # signatures) in history so the next round is valid.
            st.session_state.api_messages.append(
                {"role": "assistant", "content": response.content}
            )

            usage = response.usage
            tok_in += usage.input_tokens or 0
            tok_out += usage.output_tokens or 0
            tok_cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
            tok_cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0

            final_stop_reason = response.stop_reason
            if response.stop_reason != "tool_use":
                break

            # Reflect tool activity in the chat bubble while tools run.
            answer_slot.markdown(answer_text or "_Working… (consulting tools)_")

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_calls_made += 1
                log_event(
                    {"kind": "tool_call", "name": block.name, "input": dict(block.input)},
                    turn_log,
                )
                output, is_error = run_tool(block.name, dict(block.input))
                log_event(
                    {
                        "kind": "tool_result",
                        "name": block.name,
                        "output": output,
                        "is_error": is_error,
                    },
                    turn_log,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )

            if not tool_results:  # defensive: tool_use with no blocks -> stop
                break

            st.session_state.api_messages.append(
                {"role": "user", "content": tool_results}
            )

    except anthropic.APIError as exc:
        msg = f"⚠️ Anthropic API error: {getattr(exc, 'message', None) or exc}"
        answer_text = answer_text or msg
        answer_slot.markdown(answer_text)
        log_event({"kind": "error", "text": msg}, turn_log)
        st.session_state.chat_log.append({"role": "assistant", "text": answer_text})
        return
    except Exception as exc:  # noqa: BLE001 - never crash the whole app on a turn
        msg = f"⚠️ Unexpected error: {exc}"
        answer_text = answer_text or msg
        answer_slot.markdown(answer_text)
        log_event({"kind": "error", "text": msg}, turn_log)
        st.session_state.chat_log.append({"role": "assistant", "text": answer_text})
        return

    if not answer_text:
        answer_text = "_(The agent finished without a textual response.)_"
    answer_slot.markdown(answer_text)

    # Token usage for the whole turn (a single summary line keeps the log tidy).
    log_event(
        {
            "kind": "usage",
            "input": tok_in,
            "output": tok_out,
            "cache_read": tok_cache_read,
            "cache_write": tok_cache_write,
        },
        turn_log,
    )

    if final_stop_reason == "max_tokens":
        log_event(
            {"kind": "status", "text": "⚠️ Response truncated (hit max_tokens)."},
            turn_log,
        )

    if tool_calls_made == 0:
        log_event(
            {"kind": "status", "text": "✅ Answered directly — no tools needed."},
            turn_log,
        )

    st.session_state.chat_log.append({"role": "assistant", "text": answer_text})


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🧠", layout="wide")
    init_state()

    # --- API key check (clear error if missing) --------------------------- #
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.title(f"🧠 {PAGE_TITLE}")
        st.error(
            "**ANTHROPIC_API_KEY is not set.**\n\n"
            "Claude needs an API key. Set it in your shell and restart the app:\n\n"
            "```bash\n"
            'export ANTHROPIC_API_KEY="sk-ant-..."\n'
            "streamlit run app.py\n"
            "```"
        )
        st.stop()

    try:
        client = get_client(api_key)
    except Exception as exc:  # noqa: BLE001
        st.title(f"🧠 {PAGE_TITLE}")
        st.error(f"Failed to initialise the Anthropic client: {exc}")
        st.stop()

    # --- Sidebar ---------------------------------------------------------- #
    with st.sidebar:
        st.header("⚙️ Controls")
        st.caption(f"Model: `{MODEL}`")
        show_thinking = st.toggle("Show agent reasoning", value=True)
        st.divider()
        st.subheader("Try asking")
        st.markdown(
            "- *What are the current system metrics?*\n"
            "- *Search the web for the latest on quantum computing.*\n"
            "- *Is the server healthy, and what's new with Rust?*\n"
            "- *Explain what a neural network is.* (no tools needed)"
        )
        st.divider()
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.api_messages = []
            st.session_state.chat_log = []
            st.session_state.activity_log = []
            st.rerun()

    # --- Header ----------------------------------------------------------- #
    st.title(f"🧠 {PAGE_TITLE}")
    st.caption(
        "Left: your conversation with the agent.  "
        "Right: the agent's live reasoning, tool calls, arguments, and status."
    )

    prompt = st.chat_input("Ask the agent something…")

    chat_col, log_col = st.columns(2, gap="large")

    # Render the existing transcript (previous turns) in each column.
    with chat_col:
        st.subheader("💬 Chat")
        if not st.session_state.chat_log and not prompt:
            st.info(
                "Send a message to start. The agent's thinking and any tool "
                "calls will appear on the right."
            )
        for message in st.session_state.chat_log:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])

    with log_col:
        st.subheader("🛰️ Agent Activity")
        if not st.session_state.activity_log and not prompt:
            st.caption("No activity yet.")
    for entry in st.session_state.activity_log:
        render_log_entry(entry, log_col)

    # Handle a new message: stream the live turn beneath the rendered history.
    if prompt:
        process_turn(client, prompt, chat_col, log_col, show_thinking)


if __name__ == "__main__":
    main()
