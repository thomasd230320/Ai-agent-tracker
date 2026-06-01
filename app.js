/*
 * AI Agent Activity Dashboard — browser simulation with an animated robot.
 * Pure client-side: no API key, no backend, no limits. Deployable as a static
 * site (e.g. on Vercel). The robot in its room animates ONLY while a task runs,
 * and rests when the task is finished.
 */
"use strict";

const AGENTS = ["Atlas", "Nova", "Orion", "Sentinel", "Echo"];

const EXAMPLE_TASKS = [
  "Check system health and flag anything unusual",
  "Research the latest in AI agents and summarise it",
  "Pull recent orders from the database and analyse the trend",
  "Investigate the spike in error rates and notify the team",
  "Find the top competitors for our product and compare them",
  "Audit current resource usage across the servers",
];

const WORD_DELAY = 14; // ms per word while "typing"
const STEP_PAUSE = 350; // ms between steps

// --- tiny helpers ---------------------------------------------------------- //
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const int = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const rnd = (a, b, d = 1) => Number((Math.random() * (b - a) + a).toFixed(d));
const nowTime = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

function sampleTwo(arr) {
  const copy = arr.slice();
  const out = [];
  for (let i = 0; i < 2 && copy.length; i++) {
    out.push(copy.splice(Math.floor(Math.random() * copy.length), 1)[0]);
  }
  return out;
}

// --- the "brain": pick tools for a task ------------------------------------ //
function deriveQuery(task) {
  const stop = new Set(["the", "a", "an", "for", "and", "to", "our", "of", "on", "in", "find", "research"]);
  const words = task.split(/\s+/).filter((w) => w && !stop.has(w.toLowerCase()));
  return words.slice(0, 6).join(" ") || task;
}

function planTools(task) {
  const t = task.toLowerCase();
  const has = (...ks) => ks.some((k) => t.includes(k));
  const plan = [];

  if (has("metric", "health", "cpu", "memory", "server", "performance", "load", "uptime", "resource", "error rate"))
    plan.push({ name: "fetch_system_metrics", args: {} });
  if (has("search", "latest", "news", "find", "research", "web", "competitor", "compare", "look up"))
    plan.push({ name: "execute_web_search", args: { query: deriveQuery(task) } });
  if (has("database", "db", "users", "records", "rows", "table", "orders", "customers", "data"))
    plan.push({ name: "query_database", args: { table: pick(["orders", "users", "events", "metrics"]) } });

  if (plan.length === 0) plan.push({ name: "execute_web_search", args: { query: deriveQuery(task) } });

  if (Math.random() < 0.75) plan.push({ name: "analyze_data", args: { subject: deriveQuery(task) } });
  if (has("notify", "alert", "email", "message", "slack", "ping", "team", "investigate"))
    plan.push({ name: "send_notification", args: { channel: "#ops", message: "Update on: " + deriveQuery(task) } });

  return plan.slice(0, 4);
}

// --- simulated tools (return plain objects) -------------------------------- //
function runSimTool(name, args) {
  if (name === "execute_web_search") {
    const q = args.query || "";
    const slug = (q.trim().replace(/\s+/g, "-").toLowerCase()) || "query";
    return {
      query: q,
      result_count: 3,
      results: [
        { title: `${q} — Overview`, url: `https://example.com/${slug}`, snippet: `A concise overview of "${q}" and recent developments.` },
        { title: `Latest on ${q}`, url: `https://news.example.com/search?q=${encodeURIComponent(q)}`, snippet: `Recent reporting related to "${q}".` },
        { title: `${q} explained`, url: `https://wiki.example.com/wiki/${slug}`, snippet: "Background, context, and FAQs." },
      ],
    };
  }
  if (name === "fetch_system_metrics") {
    return {
      cpu_percent: rnd(3, 95, 1),
      memory_percent: rnd(28, 93, 1),
      disk_percent: rnd(40, 88, 1),
      active_connections: int(12, 480),
      error_rate_per_min: rnd(0, 14, 2),
      uptime_hours: rnd(1, 1200, 1),
      sampled_at: new Date().toISOString(),
    };
  }
  if (name === "query_database") {
    const n = int(3, 9);
    const names = ["Alice", "Bob", "Chen", "Dara", "Esa"];
    const sample = Array.from({ length: n }, (_, i) => ({ id: 1000 + i, name: pick(names), value: rnd(10, 999, 2) }));
    return { table: args.table, row_count: n, sample };
  }
  if (name === "analyze_data") {
    return {
      subject: args.subject,
      insights: sampleTwo([
        "trend is rising week over week",
        "two outliers detected and excluded",
        "strong correlation with traffic volume",
        "no anomalies in the latest window",
        "seasonality accounts for most variance",
      ]),
      confidence: rnd(0.72, 0.98, 2),
    };
  }
  if (name === "send_notification") {
    return { channel: args.channel, delivered: true, message: args.message, at: new Date().toISOString() };
  }
  return { error: `unknown tool '${name}'` };
}

function narrationFor(name, args) {
  switch (name) {
    case "fetch_system_metrics": return "Checking live system metrics to assess current health.";
    case "execute_web_search": return `Searching the web for "${args.query}" to gather context.`;
    case "query_database": return `Querying the \`${args.table}\` table for relevant records.`;
    case "analyze_data": return `Analysing the gathered data on "${args.subject}".`;
    case "send_notification": return `Sending a status update to ${args.channel}.`;
    default: return "Working on the next step.";
  }
}

function composeAnswer(agent, findings) {
  const parts = [];
  for (const [name, d] of findings) {
    if (name === "fetch_system_metrics") {
      const hot = d.cpu_percent > 80 || d.memory_percent > 85 || d.error_rate_per_min > 8;
      parts.push(`system health looks ${hot ? "⚠️ elevated" : "✅ healthy"} (CPU ${d.cpu_percent}%, memory ${d.memory_percent}%, errors ${d.error_rate_per_min}/min)`);
    } else if (name === "execute_web_search") {
      parts.push(`found ${d.result_count} relevant sources on "${d.query}"`);
    } else if (name === "query_database") {
      parts.push(`retrieved ${d.row_count} rows from ${d.table}`);
    } else if (name === "analyze_data") {
      parts.push(`analysed the data (${Math.round(d.confidence * 100)}% confidence: ${d.insights[0]})`);
    } else if (name === "send_notification") {
      parts.push(`notified the team in ${d.channel}`);
    }
  }
  if (!parts.length) return `${agent} finished, but had nothing notable to report.`;
  return `Task complete. ${agent} ${parts.join("; ")}. Let me know if you'd like a deeper dive.`;
}

// --- DOM plumbing ---------------------------------------------------------- //
const chatEl = () => document.getElementById("chat");
const activityEl = () => document.getElementById("activity");
const scrollDown = (node) => { node.scrollTop = node.scrollHeight; };

function addChat(role, html) {
  const wrap = document.createElement("div");
  wrap.className = "bubble " + role;
  wrap.innerHTML = html;
  chatEl().appendChild(wrap);
  scrollDown(chatEl());
  return wrap;
}

function addActivity(kind) {
  const node = document.createElement("div");
  node.className = "entry " + kind;
  activityEl().appendChild(node);
  scrollDown(activityEl());
  return node;
}

function codeBlock(obj) {
  const pre = document.createElement("pre");
  pre.className = "code";
  pre.textContent = JSON.stringify(obj, null, 2);
  return pre;
}

async function streamInto(node, text, fast = false) {
  const words = text.split(" ");
  let acc = "";
  for (const w of words) {
    acc += w + " ";
    node.textContent = acc;
    scrollDown(node.closest(".scroll") || activityEl());
    await sleep(fast ? 8 : WORD_DELAY);
  }
  node.textContent = text;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// --- the robot in its room ------------------------------------------------- //
function setRobot(working, text) {
  const room = document.getElementById("room");
  if (room) room.classList.toggle("working", !!working);
  if (text != null) {
    const b = document.getElementById("robotBubble");
    if (b) b.textContent = text;
  }
}

function sizeRoom() {
  const room = document.getElementById("room");
  const robot = document.getElementById("robot");
  if (!room || !robot) return;
  const span = Math.max(40, room.clientWidth - robot.offsetWidth - 56);
  room.style.setProperty("--span", span + "px");
}

// --- the agent run --------------------------------------------------------- //
let running = false;

function setBusy(busy) {
  running = busy;
  document.getElementById("taskInput").disabled = busy;
  document.querySelectorAll("button").forEach((b) => (b.disabled = busy));
}

async function runTask(task) {
  if (running || !task.trim()) return;
  setBusy(true);
  const agent = pick(AGENTS);
  setRobot(true, `🤖 ${agent} — on it!`); // robot starts working

  addChat("user", `<span class="label">Task</span>${escapeHtml(task)}`);
  const assistant = addChat("agent", `<div class="status">🟢 <b>Agent ${agent}</b> is on it…</div><div class="answer"></div>`);

  const status = addActivity("status");
  status.textContent = `▶️ ${agent} assigned · ${nowTime()}`;
  scrollDown(activityEl());

  const plan = planTools(task);
  const findings = [];

  for (const step of plan) {
    setRobot(true, "💭 thinking…");
    const narr = addActivity("narration");
    await streamInto(narr, "💭 " + narrationFor(step.name, step.args));

    setRobot(true, "🛠️ " + step.name);
    const call = addActivity("tool_call");
    call.innerHTML = `<div class="head">🛠️ Tool call: <code>${escapeHtml(step.name)}</code></div>`;
    call.appendChild(codeBlock(step.args));
    scrollDown(activityEl());
    await sleep(STEP_PAUSE);

    const out = runSimTool(step.name, step.args);
    const res = addActivity("tool_result");
    res.innerHTML = `<div class="head">✅ <code>${escapeHtml(step.name)}</code> completed</div>`;
    res.appendChild(codeBlock(out));
    scrollDown(activityEl());
    findings.push([step.name, out]);
    await sleep(STEP_PAUSE);
  }

  assistant.querySelector(".status").innerHTML = `✅ <b>Agent ${agent}</b> finished.`;
  await streamInto(assistant.querySelector(".answer"), composeAnswer(agent, findings), true);

  const done = addActivity("status");
  done.textContent = `🏁 ${agent} completed ${plan.length} step(s).`;
  scrollDown(activityEl());

  // task finished → robot stops and rests
  setRobot(false, "✅ done!");
  setBusy(false);
  setTimeout(() => { if (!running) setRobot(false, "💤 idle"); }, 1600);
  document.getElementById("taskInput").focus();
}

// --- wire up the UI -------------------------------------------------------- //
function init() {
  sizeRoom();
  window.addEventListener("resize", sizeRoom);

  const chips = document.getElementById("chips");
  EXAMPLE_TASKS.slice(0, 4).forEach((t) => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = t;
    chip.addEventListener("click", () => runTask(t));
    chips.appendChild(chip);
  });

  document.getElementById("taskForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("taskInput");
    const value = input.value;
    input.value = "";
    runTask(value);
  });

  document.getElementById("randomBtn").addEventListener("click", () => runTask(pick(EXAMPLE_TASKS)));
  document.getElementById("clearBtn").addEventListener("click", () => {
    chatEl().innerHTML = "";
    activityEl().innerHTML = "";
    setRobot(false, "💤 idle");
  });
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", init);
}
