const API_URL = "/chat"; // Flask endpoint

const state = {
  preset: "Blog Post",
  lastPrompt: null,
  history: [],
};

const $ = (id) => document.getElementById(id);
const presetsEl = $("presets");
const outputEl = $("output");
const historyEl = $("history");
const toastEl = $("toast");

presetsEl.addEventListener("click", (e) => {
  const li = e.target.closest(".preset");
  if (!li) return;
  document.querySelectorAll(".preset").forEach(p => p.classList.remove("active"));
  li.classList.add("active");
  state.preset = li.dataset.preset;
});

$("generate").addEventListener("click", () => generate());
$("regen").addEventListener("click", () => {
  if (state.lastPrompt) sendPrompt(state.lastPrompt);
  else toast("Nothing to regenerate yet");
});
$("clear").addEventListener("click", () => {
  $("topic").value = "";
  $("audience").value = "";
  outputEl.innerHTML = '<div class="empty">Your generated content will appear here.</div>';
});
$("copy").addEventListener("click", async () => {
  const text = outputEl.innerText.trim();
  if (!text || text.startsWith("Your generated")) return toast("Nothing to copy");
  try { await navigator.clipboard.writeText(text); toast("Copied to clipboard ✓"); }
  catch { toast("Copy failed"); }
});

function buildPrompt() {
  const topic = $("topic").value.trim();
  if (!topic) { toast("Enter a topic first"); return null; }
  const tone = $("tone").value;
  const length = $("length").value;
  const audience = $("audience").value.trim();
  let p = `Write a ${length.toLowerCase()} ${state.preset} in a ${tone.toLowerCase()} tone`;
  if (audience) p += ` for ${audience}`;
  p += ` about: ${topic}.`;
  p += ` Format the output cleanly with headings or bullet points where appropriate.`;
  return p;
}

async function generate() {
  const prompt = buildPrompt();
  if (!prompt) return;
  state.lastPrompt = prompt;
  await sendPrompt(prompt);
}

async function sendPrompt(prompt) {
  const btn = $("generate");
  btn.disabled = true;
  outputEl.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Server error (${res.status})`);
    }

    const data = await res.json();
    const reply = data.reply || data.message || "(empty response)";
    outputEl.textContent = reply;
    addHistory(prompt, reply);
  } catch (err) {
    outputEl.innerHTML = `<div class="empty">⚠️ ${err.message}</div>`;
    toast(err.message);
  } finally {
    btn.disabled = false;
  }
}

function addHistory(prompt, reply) {
  state.history.unshift({ prompt, reply });
  state.history = state.history.slice(0, 12);
  renderHistory();
}

function renderHistory() {
  historyEl.innerHTML = "";
  state.history.forEach((h, i) => {
    const li = document.createElement("li");
    li.textContent = h.prompt.slice(0, 40) + (h.prompt.length > 40 ? "…" : "");
    li.title = h.prompt;
    li.addEventListener("click", () => { outputEl.textContent = h.reply; });
    historyEl.appendChild(li);
  });
}

let toastTimer;
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2600);
}
