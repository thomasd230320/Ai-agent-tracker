"""
AI Agent Activity Dashboard  (powered by Google Gemini — free tier)
===================================================================

A single-file Streamlit app that lets you launch an AI agent and **watch it
work in real time**. The screen is split into two side-by-side columns:

  • Left  — 🎯 Tasks & Results: the task you give the agent and its final answer.
  • Right — 🛰️ Live Agent Activity: a streaming log of what the agent is doing —
            its narration, the tools it calls, the arguments it passes, and the
            status of each call — as it happens, before the final answer.

It uses Google's **Gemini** API (the free tier from https://aistudio.google.com)
with function calling (tools) and streaming. Two mock tools are provided:
``execute_web_search(query)`` and ``fetch_system_metrics()``.

Run it:

    pip install -r requirements.txt          # streamlit + google-genai
    # then provide a free Gemini API key (https://aistudio.google.com → Get API key):
    export GEMINI_API_KEY="AIza..."           # or put it in Streamlit Secrets
    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Lighter model with its own free-tier quota — a good choice when the standard
# flash model hits a spend/usage cap. Other options to try if needed:
# "gemini-1.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash".
MODEL = "gemini-2.0-flash-lite"

# Safety cap on the agent's autonomous tool loop (think -> call tool -> repeat).
MAX_STEPS = 8

PAGE_TITLE = "AI Agent Activity Dashboard"

SYSTEM_PROMPT = (
    "You are an autonomous AI agent whose activity is being watched on a live "
    "dashboard. Carry out the user's task step by step.\n\n"
    "You have two tools:\n"
    "  • execute_web_search(query) — look up current or external information.\n"
    "  • fetch_system_metrics()    — read live host metrics (CPU, memory, etc.).\n\n"
    "Briefly narrate what you are about to do before calling a tool, call a tool "
    "only when it genuinely helps, and once you have what you need, give a clear, "
    "concise final answer for the user."
)

# --------------------------------------------------------------------------- #
# Tool definitions (sent to Gemini) and their local mock implementations
# --------------------------------------------------------------------------- #

GENAI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="execute_web_search",
                description=(
                    "Search the web for up-to-date information. Use this when the "
                    "task involves current events, recent facts, prices, libraries, "
                    "or anything needing fresh external data."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="The search query to run.",
                        )
                    },
                    required=["query"],
                ),
            ),
            types.FunctionDeclaration(
                name="fetch_system_metrics",
                description=(
                    "Fetch a snapshot of live system metrics (CPU, memory, disk, "
                    "network, uptime). Use this when the task involves system "
                    "health, performance, load, or resource usage."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT, properties={}, required=[]
                ),
            ),
        ]
    )
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
    except Exception as exc:  # noqa: BLE001 - surface any failure back to the model
        return f"Error while executing '{name}': {exc}", True


# --------------------------------------------------------------------------- #
# Session state & client
# --------------------------------------------------------------------------- #


def init_state() -> None:
    """Initialise the persistent state used across Streamlit reruns."""
    # Raw Gemini conversation history (list[types.Content]) — source of truth.
    st.session_state.setdefault("contents", [])
    # Left column: list of {"role": ..., "text": ...} for the task/result log.
    st.session_state.setdefault("chat_log", [])
    # Right column: list of structured activity entries.
    st.session_state.setdefault("activity_log", [])


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    """Create (and cache) the Gemini client for the given key."""
    return genai.Client(api_key=api_key)


def resolve_api_key() -> str | None:
    """Find the Gemini API key from Streamlit secrets or the environment.

    Works on Streamlit Community Cloud (key set under *Settings → Secrets*) and
    locally (a ``.streamlit/secrets.toml`` file or an env var). Accepts either
    ``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``.
    """
    try:
        # Accessing st.secrets raises if no secrets file/config exists, so guard it.
        for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if key in st.secrets:
                return str(st.secrets[key])
    except Exception:  # noqa: BLE001 - "no secrets configured" is a normal case
        pass
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


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

    elif kind == "narration":
        c.markdown(f"💭 _{entry['text']}_")

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
        c.caption(
            "📊 tokens — "
            f"in {entry['input']} · out {entry['output']} · total {entry['total']}"
        )

    elif kind == "error":
        c.error(entry["text"])


def log_event(entry: dict, c) -> None:
    """Persist an activity entry for future reruns *and* render it live now."""
    st.session_state.activity_log.append(entry)
    render_log_entry(entry, c)


# --------------------------------------------------------------------------- #
# Core agent loop
# --------------------------------------------------------------------------- #


def process_turn(client, prompt: str, chat_col, log_col) -> None:
    """Run the agent autonomously for one task, streaming activity live.

    Streams the agent's narration and tool activity into ``log_col`` and its
    final answer into ``chat_col``, feeding tool results back to Gemini until
    the agent stops calling tools (or hits ``MAX_STEPS``).
    """
    st.session_state.chat_log.append({"role": "user", "text": prompt})
    st.session_state.contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    )

    with chat_col:
        with st.chat_message("user"):
            st.markdown(prompt)
        assistant_box = st.chat_message("assistant")
    with assistant_box:
        answer_slot = st.empty()
    answer_slot.markdown("_Agent is working…_")

    turn_log = log_col.container()
    log_event(
        {"kind": "status", "text": f"▶️ Task received · {datetime.now():%H:%M:%S}"},
        turn_log,
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=GENAI_TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.6,
    )

    answer_text = ""
    tool_calls_made = 0
    usage_meta = None

    try:
        for step in range(MAX_STEPS):
            narration_slot = turn_log.empty()
            text_buf = ""
            thought_buf = ""
            function_calls = []

            stream = client.models.generate_content_stream(
                model=MODEL,
                contents=st.session_state.contents,
                config=config,
            )
            for chunk in stream:
                if getattr(chunk, "usage_metadata", None):
                    usage_meta = chunk.usage_metadata
                candidates = getattr(chunk, "candidates", None) or []
                if not candidates:
                    continue
                content = candidates[0].content
                if not content or not content.parts:
                    continue
                for part in content.parts:
                    call = getattr(part, "function_call", None)
                    if call is not None:
                        function_calls.append(call)
                        continue
                    txt = getattr(part, "text", None)
                    if not txt:
                        continue
                    if getattr(part, "thought", False):
                        thought_buf += txt
                    else:
                        text_buf += txt
                    disp = ""
                    if thought_buf.strip():
                        disp += "🧠 _" + thought_buf.strip() + "_\n\n"
                    if text_buf.strip():
                        disp += "💭 **Agent:** " + text_buf.strip()
                    narration_slot.markdown(disp or "💭 …")

            # Rebuild the model's turn for history (text + any tool calls).
            model_parts = []
            if text_buf:
                model_parts.append(types.Part.from_text(text=text_buf))
            for call in function_calls:
                model_parts.append(types.Part(function_call=call))
            if model_parts:
                st.session_state.contents.append(
                    types.Content(role="model", parts=model_parts)
                )

            if thought_buf.strip():
                st.session_state.activity_log.append(
                    {"kind": "thinking", "text": thought_buf.strip()}
                )

            if not function_calls:
                # Final step: this text is the answer (it belongs on the left).
                answer_text = text_buf.strip()
                narration_slot.empty()
                break

            # Tool step: the narration belongs in the activity log.
            if text_buf.strip():
                st.session_state.activity_log.append(
                    {"kind": "narration", "text": text_buf.strip()}
                )
            answer_slot.markdown("_Agent is using tools…_")

            response_parts = []
            for call in function_calls:
                tool_calls_made += 1
                args = dict(call.args) if call.args else {}
                log_event(
                    {"kind": "tool_call", "name": call.name, "input": args}, turn_log
                )
                output, is_error = run_tool(call.name, args)
                log_event(
                    {
                        "kind": "tool_result",
                        "name": call.name,
                        "output": output,
                        "is_error": is_error,
                    },
                    turn_log,
                )
                response_parts.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"error": output} if is_error else {"result": output},
                    )
                )

            st.session_state.contents.append(
                types.Content(role="user", parts=response_parts)
            )
        else:
            log_event(
                {"kind": "status", "text": f"⚠️ Stopped after {MAX_STEPS} steps."},
                turn_log,
            )

    except Exception as exc:  # noqa: BLE001 - never crash the app on a turn
        msg = f"⚠️ Gemini error: {exc}"
        answer_text = answer_text or msg
        answer_slot.markdown(answer_text)
        log_event({"kind": "error", "text": msg}, turn_log)
        st.session_state.chat_log.append({"role": "assistant", "text": answer_text})
        return

    if not answer_text:
        answer_text = "_(The agent finished without a final message.)_"
    answer_slot.markdown(answer_text)

    if usage_meta is not None:
        log_event(
            {
                "kind": "usage",
                "input": getattr(usage_meta, "prompt_token_count", 0) or 0,
                "output": getattr(usage_meta, "candidates_token_count", 0) or 0,
                "total": getattr(usage_meta, "total_token_count", 0) or 0,
            },
            turn_log,
        )

    if tool_calls_made == 0:
        log_event(
            {"kind": "status", "text": "✅ Answered directly — no tools used."},
            turn_log,
        )

    st.session_state.chat_log.append({"role": "assistant", "text": answer_text})


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🛰️", layout="wide")
    init_state()

    # --- API key check (clear error if missing) --------------------------- #
    api_key = resolve_api_key()
    if not api_key:
        st.title(f"🛰️ {PAGE_TITLE}")
        st.error(
            "**No Gemini API key found.** Get a free one at "
            "[aistudio.google.com](https://aistudio.google.com) → **Get API key**, "
            "then provide it one of these ways:\n\n"
            "**Streamlit Community Cloud** — app menu → **Settings → Secrets**:\n\n"
            "```toml\n"
            'GEMINI_API_KEY = "AIza..."\n'
            "```\n"
            "**Local** — set an environment variable, then restart:\n\n"
            "```bash\n"
            'export GEMINI_API_KEY="AIza..."\n'
            "streamlit run app.py\n"
            "```"
        )
        st.stop()

    try:
        client = get_client(api_key)
    except Exception as exc:  # noqa: BLE001
        st.title(f"🛰️ {PAGE_TITLE}")
        st.error(f"Failed to initialise the Gemini client: {exc}")
        st.stop()

    # --- Sidebar ---------------------------------------------------------- #
    with st.sidebar:
        st.header("⚙️ Controls")
        st.caption(f"Provider: **Google Gemini** (free tier)")
        st.caption(f"Model: `{MODEL}`")
        st.divider()
        st.subheader("Try a task")
        st.markdown(
            "- *Check the current system metrics and tell me if anything looks high.*\n"
            "- *Search the web for the latest on quantum computing and summarise it.*\n"
            "- *Is the server healthy, and what's new with Rust?*\n"
            "- *Explain what a neural network is.* (no tools needed)"
        )
        st.divider()
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.contents = []
            st.session_state.chat_log = []
            st.session_state.activity_log = []
            st.rerun()

    # --- Header ----------------------------------------------------------- #
    st.title(f"🛰️ {PAGE_TITLE}")
    st.caption(
        "Give the agent a task and watch it work.  "
        "Left: the task and final result.  "
        "Right: the agent's live activity — narration, tool calls, and status."
    )

    prompt = st.chat_input("Give the agent a task to run…")

    chat_col, log_col = st.columns(2, gap="large")

    # Render the existing history (previous tasks) in each column.
    with chat_col:
        st.subheader("🎯 Tasks & Results")
        if not st.session_state.chat_log and not prompt:
            st.info(
                "Give the agent a task to start. Its live activity — thinking, "
                "tool calls, and status — appears on the right."
            )
        for message in st.session_state.chat_log:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])

    with log_col:
        st.subheader("🛰️ Live Agent Activity")
        if not st.session_state.activity_log and not prompt:
            st.caption("No activity yet.")
    for entry in st.session_state.activity_log:
        render_log_entry(entry, log_col)

    # Handle a new task: stream the live run beneath the rendered history.
    if prompt:
        process_turn(client, prompt, chat_col, log_col)


if __name__ == "__main__":
    main()
