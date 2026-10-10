/* ==========================================================================
   Query-X  |  script.js   (all the behaviour of the page)
   --------------------------------------------------------------------------
   HOW THE FILE IS ORGANISED (read in this order):
     1. CONFIG        -> settings you may want to change (API URL, demo mode)
     2. TEXT          -> English / Hindi words used by the interface
     3. STATE         -> the data we keep in memory (chats, messages)
     4. HELPERS       -> small utility functions
     5. TALKING TO THE BACKEND  (askBackend, mock demo answers)
     6. SENDING A MESSAGE       (the main flow)
     7. DRAWING THE SCREEN      (renderChatList, renderMessages, renderSources)
     8. CHAT HISTORY            (new chat, open chat, delete, clear)
     9. FEEDBACK / COPY / RETRY
    10. VOICE INPUT
    11. EVENT LISTENERS (buttons, keyboard)

   BIG IDEA: we never edit the screen piece by piece. We change the STATE
   (the data) and then call render...() which redraws the screen from it.
   This keeps the code simple and avoids bugs.
   ========================================================================== */

/* ---------- 1. CONFIG ---------- */
const CONFIG = {
  API_URL: "/api/chat",          // Python endpoint that answers questions
  FEEDBACK_URL: "/api/feedback", // Python endpoint that stores thumbs up/down
  PDF_BASE_URL: "/pdf/",         // Where PDFs are served from (see server.py)
  USE_MOCK: true,                // true = fake answers (demo). Set false when backend is ready
  TIMEOUT_MS: 30000,             // give up if backend takes longer than 30 seconds
  HISTORY_TURNS: 6,              // how many previous messages we send for follow-up questions
};

// Remember settings changed in the Settings popup (kept after refresh)
try {
  const saved = JSON.parse(localStorage.getItem("queryx-config") || "{}");
  Object.assign(CONFIG, saved);
} catch (e) { /* ignore broken saved data */ }

/* ---------- 2. TEXT (English + Hindi) ---------- */
const TEXT = {
  en: {
    placeholder: "Ask anything about your campus...",
    hint: "Enter to send · Shift + Enter for a new line",
    tip: "You can also ask in Hindi, e.g. “कैंपस इवेंट कब है?”",
    you: "You",
    bot: "Query-X",
    welcomeTitle: "Hi! I'm Query-X 👋",
    welcomeBody: "Ask me anything about your campus. My answers come from the college documents, and I'll show you the source.",
    suggestions: ["Where can I find information about the campus event?", "What are the hostel facilities?", "When is the exam schedule?"],
    emptyChats: "No chats yet",
    newChat: "New chat",
    fallback: "I couldn't find this in the documents I have, so I don't want to guess. Try rephrasing the question or ask about something else.",
    errNetwork: "Sorry, I couldn't reach the server. Please check that the backend is running and try again.",
    errTimeout: "The server took too long to respond. Please try again.",
    errServer: "Something went wrong on the server. Please try again.",
    emptyQ: "Please type a question first.",
    noVoice: "Voice input is not supported in this browser. Please use Chrome or Edge.",
    micDenied: "Microphone permission was blocked. Allow it in the browser address bar and try again.",
    listening: "Listening...",
    confirmClear: "Delete ALL chats of this session?",
    copied: "Copied!",
    viewPdf: "View PDF",
    expand: "Show more",
    collapse: "Show less",
    page: "Page",
  },
  hi: {
    placeholder: "अपने कैंपस के बारे में कुछ भी पूछें...",
    hint: "भेजने के लिए Enter · नई लाइन के लिए Shift + Enter",
    tip: "आप अंग्रेज़ी में भी पूछ सकते हैं, जैसे “Where is the Tech Fest held?”",
    you: "आप",
    bot: "Query-X",
    welcomeTitle: "नमस्ते! मैं Query-X हूँ 👋",
    welcomeBody: "कैंपस के बारे में कुछ भी पूछिए। मेरे उत्तर कॉलेज के दस्तावेज़ों से आते हैं और मैं स्रोत भी दिखाऊँगा।",
    suggestions: ["कैंपस इवेंट के बारे में जानकारी कहाँ मिलेगी?", "हॉस्टल की सुविधाएँ क्या हैं?", "परीक्षा का समय-सारणी क्या है?"],
    emptyChats: "अभी कोई चैट नहीं",
    newChat: "नई चैट",
    fallback: "यह जानकारी मुझे उपलब्ध दस्तावेज़ों में नहीं मिली, इसलिए मैं अंदाज़ा नहीं लगाना चाहता। कृपया प्रश्न दूसरे शब्दों में पूछें।",
    errNetwork: "क्षमा करें, सर्वर से संपर्क नहीं हो सका। कृपया जाँचें कि बैकएंड चालू है और फिर कोशिश करें।",
    errTimeout: "सर्वर ने जवाब देने में बहुत समय लिया। कृपया फिर कोशिश करें।",
    errServer: "सर्वर पर कुछ गड़बड़ हो गई। कृपया फिर कोशिश करें।",
    emptyQ: "कृपया पहले कोई प्रश्न लिखें।",
    noVoice: "इस ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं है। कृपया Chrome या Edge का उपयोग करें।",
    micDenied: "माइक्रोफ़ोन की अनुमति बंद है। ब्राउज़र में अनुमति देकर फिर कोशिश करें।",
    listening: "सुन रहा हूँ...",
    confirmClear: "इस सत्र की सभी चैट हटाएँ?",
    copied: "कॉपी हो गया!",
    viewPdf: "PDF देखें",
    expand: "और दिखाएँ",
    collapse: "कम दिखाएँ",
    page: "पृष्ठ",
  },
};

/* ---------- 3. STATE ---------- */
/*
  chats = [
    { id: "c1", title: "Campus event...", messages: [
        { role: "user", text: "..." , time: 1700000000000 },
        { role: "bot",  text: "...", sources: [...], kind: "ok"|"fallback"|"error",
          feedback: "up"|"down"|null, time: ... }
    ]}
  ]
  "Session-based" history: sessionStorage is wiped when the tab is closed.
  To make history permanent later, just change sessionStorage -> localStorage
  (or save chats in your Python backend / database).
*/
const state = {
  chats: [],
  activeId: null,
  loading: false,        // true while waiting for the backend
  lang: "en",
  activeSourcesMsg: null // which bot message's sources are shown in the right panel
};

function saveState() {
  try { sessionStorage.setItem("queryx-chats", JSON.stringify({ chats: state.chats, activeId: state.activeId })); }
  catch (e) { /* storage full or blocked: ignore */ }
}
function loadState() {
  try {
    const raw = JSON.parse(sessionStorage.getItem("queryx-chats") || "null");
    if (raw && Array.isArray(raw.chats)) { state.chats = raw.chats; state.activeId = raw.activeId; }
  } catch (e) { /* ignore */ }
}

/* ---------- 4. HELPERS ---------- */
const $ = (id) => document.getElementById(id);          // shortcut for getElementById
const t = (key) => TEXT[state.lang][key];                // get text in current language

// Create an element safely. We use textContent (NOT innerHTML) so that
// text coming from the backend/user can never inject HTML or scripts.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const uid = () => "c" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
const fmtTime = (ms) => new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const activeChat = () => state.chats.find((c) => c.id === state.activeId);

/* ---------- 5. TALKING TO THE BACKEND ---------- */
/*
  REQUEST we send (JSON, POST):
    { question: "Where is it held?",
      language: "en" | "hi",
      history: [ {role:"user", text:"..."}, {role:"bot", text:"..."} ]   <- last few messages
    }
  RESPONSE we expect (JSON):
    { answer: "text",
      supported: true,                     // false if documents don't support an answer
      sources: [ { file:"Campus Events.pdf", page:2, section:"Student activities",
                   snippet:"exact passage text..." } ] }
  The python side must do the multi-turn work (e.g. rewrite "it" using history).
*/
async function askBackend(question, history) {
  if (CONFIG.USE_MOCK) return mockBackend(question, history);

  // AbortController lets us cancel the request after TIMEOUT_MS
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), CONFIG.TIMEOUT_MS);

  try {
    const res = await fetch(CONFIG.API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, language: state.lang, history }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error("HTTP " + res.status);   // 400/500 etc.
    return await res.json();
  } finally {
    clearTimeout(timer); // always stop the timer
  }
}

/* DEMO MODE: fake backend so the UI can be shown without Python running. */
function mockBackend(question, history) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const q = question.toLowerCase();
      // Follow-up demo: "where is it held" after talking about the tech fest
      const lastBot = [...history].reverse().find((m) => m.role === "bot");
      const talkingAboutFest = lastBot && /tech fest/i.test(lastBot.text);

      if (/(event|fest|कैंपस इवेंट|इवेंट)/i.test(q) && !/(where|held|कहाँ)/i.test(q)) {
        resolve({
          answer: "The major event this year is the Annual Tech Fest, which will be held from April 15–17, 2025 at the main auditorium.",
          supported: true,
          sources: [{
            file: "Campus Events.pdf", page: 2, section: "Student activities",
            snippet: "The Annual Tech Fest 2025 will be held from April 15–17, 2025 at the main auditorium. Various technical and cultural events will be organized during the festival.",
          }],
        });
      } else if (talkingAboutFest && /(where|held|कहाँ)/i.test(q)) {
        resolve({
          answer: "The Annual Tech Fest is held at the main auditorium.",
          supported: true,
          sources: [{
            file: "Campus Events.pdf", page: 2, section: "Student activities",
            snippet: "The Annual Tech Fest 2025 will be held from April 15–17, 2025 at the main auditorium.",
          }],
        });
      } else if (/hostel/i.test(q)) {
        resolve({
          answer: "Hostels provide Wi-Fi, a common mess, a study room and 24x7 security.",
          supported: true,
          sources: [{ file: "Hostel Guide.pdf", page: 4, section: "Facilities",
            snippet: "All hostels offer Wi-Fi, a common mess, a study room and 24x7 security." }],
        });
      } else {
        // Nothing matched -> behave like a real RAG bot that found no support
        resolve({ answer: "", supported: false, sources: [] });
      }
    }, 1200); // fake delay so the loading animation is visible
  });
}

/* ---------- 6. SENDING A MESSAGE (main flow) ---------- */
async function sendMessage(rawText) {
  const text = (rawText || "").trim();

  // Reliable fallback #1: empty question
  if (!text) { flashHint(t("emptyQ")); return; }
  if (state.loading) return;                 // ignore clicks while waiting

  // Make sure a chat exists (first message creates one)
  let chat = activeChat();
  if (!chat) chat = createChat();

  // Name the chat after its first question
  if (chat.messages.length === 0) chat.title = text.length > 32 ? text.slice(0, 32) + "…" : text;

  chat.messages.push({ role: "user", text, time: Date.now() });
  $("input").value = ""; autoGrow();
  await getAnswer(chat);
}

/* Asks the backend using the chat's messages and adds the bot reply.
   Used by sendMessage() and by the Retry button. */
async function getAnswer(chat) {
  state.loading = true;
  updateSendState();
  renderChatList(); renderMessages();

  const lastUser = [...chat.messages].reverse().find((m) => m.role === "user");
  // Multi-turn memory: send the previous messages (everything BEFORE this question)
  const idx = chat.messages.lastIndexOf(lastUser);
  const history = chat.messages
    .slice(Math.max(0, idx - CONFIG.HISTORY_TURNS), idx)
    .filter((m) => m.kind !== "error")
    .map((m) => ({ role: m.role, text: m.text }));

  let botMsg;
  try {
    const data = await askBackend(lastUser.text, history);
    const sources = Array.isArray(data.sources) ? data.sources : [];

    // Reliable fallback #2: answer is only trusted if it has supporting sources.
    // An answer with NO source could be a hallucination, so we replace it.
    const supported = data.supported !== false && sources.length > 0 && !!(data.answer || "").trim();

    botMsg = supported
      ? { role: "bot", text: data.answer, sources, kind: "ok" }
      : { role: "bot", text: t("fallback"), sources: [], kind: "fallback" };

  } catch (err) {
    // Reliable fallback #3: network error, timeout, server crash
    const msg = err.name === "AbortError" ? t("errTimeout")
              : /HTTP 5/.test(err.message) ? t("errServer")
              : t("errNetwork");
    botMsg = { role: "bot", text: msg, sources: [], kind: "error" };
  }

  botMsg.time = Date.now();
  botMsg.feedback = null;
  chat.messages.push(botMsg);
  state.activeSourcesMsg = botMsg;

  state.loading = false;
  updateSendState();
  saveState(); renderChatList(); renderMessages(); renderSources();
}

/* ---------- 7. DRAWING THE SCREEN ---------- */

/* 7a. Left sidebar: list of chats */
function renderChatList() {
  const list = $("chatList");
  list.innerHTML = "";
  const chats = state.chats.filter((c) => c.messages.length > 0);

  if (chats.length === 0) { list.appendChild(el("li", "empty-list", t("emptyChats"))); return; }

  // newest chat first
  [...chats].reverse().forEach((c) => {
    const li = el("li", "chat-item" + (c.id === state.activeId ? " active" : ""));
    li.appendChild(el("span", "title", c.title));

    const del = el("button", "del", "✕");
    del.title = "Delete this chat";
    del.addEventListener("click", (e) => { e.stopPropagation(); deleteChat(c.id); });
    li.appendChild(del);

    li.addEventListener("click", () => openChat(c.id));
    list.appendChild(li);
  });
}

/* 7b. Middle column: all messages */
function renderMessages() {
  const box = $("messages");
  box.innerHTML = "";
  const chat = activeChat();

  // Empty chat -> welcome screen with clickable example questions
  if (!chat || chat.messages.length === 0) {
    const w = el("div", "welcome");
    w.appendChild(el("h3", "", t("welcomeTitle")));
    w.appendChild(el("p", "", t("welcomeBody")));
    const s = el("div", "suggestions");
    t("suggestions").forEach((q) => {
      const b = el("button", "chip", q);
      b.addEventListener("click", () => sendMessage(q));
      s.appendChild(b);
    });
    w.appendChild(s);
    box.appendChild(w);
    return;
  }

  chat.messages.forEach((m, i) => box.appendChild(buildMessage(m, i, chat)));

  // Loading animation (three bouncing dots) while waiting for the answer
  if (state.loading) {
    const row = el("div", "msg bot");
    row.appendChild(el("div", "avatar", "QX"));
    const wrap = el("div", "bubble-wrap");
    const bubble = el("div", "bubble");
    const dots = el("div", "typing");
    dots.append(el("span"), el("span"), el("span"));
    bubble.appendChild(dots);
    wrap.appendChild(bubble);
    row.appendChild(wrap);
    box.appendChild(row);
  }

  box.scrollTop = box.scrollHeight; // always show the newest message
}

/* Builds ONE message row (avatar + bubble + sources + buttons) */
function buildMessage(m, index, chat) {
  const isBot = m.role === "bot";
  const row = el("div", "msg " + (isBot ? "bot" : "user") + (m.kind === "fallback" ? " fallback" : "") + (m.kind === "error" ? " error" : ""));

  row.appendChild(el("div", "avatar", isBot ? "QX" : "You".slice(0, 1)));

  const wrap = el("div", "bubble-wrap");
  const who = el("div", "who");
  who.appendChild(el("strong", "", isBot ? t("bot") : t("you")));
  who.appendChild(el("span", "", fmtTime(m.time)));
  wrap.appendChild(who);
  wrap.appendChild(el("div", "bubble", m.text));

  if (isBot) {
    // Inline sources: click the line to expand and read the exact passage
    if (m.sources && m.sources.length) {
      const holder = el("div", "src-inline");
      m.sources.forEach((s) => {
        const d = document.createElement("details");
        d.appendChild(el("summary", "", "📄 " + s.file + " · " + t("page") + " " + s.page + (s.section ? " · " + s.section : "")));
        d.appendChild(el("div", "snippet", s.snippet || ""));
        // when opened, also show it in the right panel
        d.addEventListener("toggle", () => { if (d.open) { state.activeSourcesMsg = m; renderSources(); } });
        holder.appendChild(d);
      });
      wrap.appendChild(holder);
    }

    // Action buttons: copy / retry / thumbs up / thumbs down
    const acts = el("div", "actions");
    if (m.kind !== "error") {
      acts.appendChild(actionBtn("📋", "Copy answer", () => copyAnswer(m, acts)));
    }
    acts.appendChild(actionBtn("🔄", "Retry", () => retry(chat, index)));
    if (m.kind === "ok") {
      acts.appendChild(actionBtn("👍", "Good answer", () => setFeedback(chat, m, "up"), m.feedback === "up"));
      acts.appendChild(actionBtn("👎", "Wrong answer", () => setFeedback(chat, m, "down"), m.feedback === "down"));
    }
    wrap.appendChild(acts);
  }

  row.appendChild(wrap);
  return row;
}

function actionBtn(icon, title, onClick, active) {
  const b = el("button", "act" + (active ? " on" : ""), icon);
  b.title = title;
  b.addEventListener("click", onClick);
  return b;
}

/* 7c. Right column: sources of the latest/selected answer */
function renderSources() {
  const list = $("sourceList");
  list.innerHTML = "";
  const m = state.activeSourcesMsg;
  const chat = activeChat();

  // Hide sources that belong to a different chat
  const belongs = m && chat && chat.messages.includes(m);
  if (!belongs || !m.sources || m.sources.length === 0) {
    list.appendChild(el("p", "muted", "Sources used for an answer will appear here."));
    return;
  }

  m.sources.forEach((s) => {
    const card = el("div", "source-card");
    card.appendChild(el("div", "file", "📄 " + s.file));
    card.appendChild(el("div", "meta", t("page") + " " + s.page + (s.section ? " • " + s.section : "")));
    card.appendChild(el("div", "snippet", s.snippet || ""));

    const btns = el("div", "source-btns");

    // Expand / collapse the passage
    const toggle = el("button", "btn-ghost", t("expand"));
    toggle.addEventListener("click", () => {
      card.classList.toggle("open");
      toggle.textContent = card.classList.contains("open") ? t("collapse") : t("expand");
    });
    btns.appendChild(toggle);

    // Open the PDF at the right page (#page=N works in Chrome/Edge/Firefox viewers)
    const view = el("a", "btn-ghost", t("viewPdf"));
    view.href = CONFIG.PDF_BASE_URL + encodeURIComponent(s.file) + "#page=" + (s.page || 1);
    view.target = "_blank";
    view.rel = "noopener";
    btns.appendChild(view);

    card.appendChild(btns);
    list.appendChild(card);
  });
}

/* ---------- 8. CHAT HISTORY ---------- */
function createChat() {
  const chat = { id: uid(), title: t("newChat"), messages: [] };
  state.chats.push(chat);
  state.activeId = chat.id;
  return chat;
}

function newChat() {
  // Reuse the current chat if it is still empty (avoids many blank chats)
  const cur = activeChat();
  if (cur && cur.messages.length === 0) { closeSidebar(); $("input").focus(); return; }
  createChat();
  state.activeSourcesMsg = null;
  saveState(); renderChatList(); renderMessages(); renderSources();
  closeSidebar(); $("input").focus();
}

function openChat(id) {
  state.activeId = id;
  const c = activeChat();
  // Show the sources of the last bot answer of that chat
  state.activeSourcesMsg = c ? [...c.messages].reverse().find((m) => m.role === "bot") || null : null;
  saveState(); renderChatList(); renderMessages(); renderSources();
  closeSidebar();
}

function deleteChat(id) {
  state.chats = state.chats.filter((c) => c.id !== id);
  if (state.activeId === id) { state.activeId = null; state.activeSourcesMsg = null; }
  saveState(); renderChatList(); renderMessages(); renderSources();
}

function clearHistory() {
  if (!state.chats.length) return;
  if (!confirm(t("confirmClear"))) return;
  state.chats = []; state.activeId = null; state.activeSourcesMsg = null;
  saveState(); renderChatList(); renderMessages(); renderSources();
}

/* ---------- 9. FEEDBACK / COPY / RETRY ---------- */
function setFeedback(chat, msg, value) {
  msg.feedback = msg.feedback === value ? null : value; // click again = undo
  saveState(); renderMessages();

  // Send to backend so testers' flags can be collected (silent if it fails)
  if (!CONFIG.USE_MOCK) {
    const i = chat.messages.indexOf(msg);
    const q = chat.messages[i - 1];
    fetch(CONFIG.FEEDBACK_URL, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q ? q.text : "", answer: msg.text, feedback: msg.feedback }),
    }).catch(() => {});
  }
}

function copyAnswer(msg, container) {
  const done = () => {
    const note = el("span", "muted", t("copied"));
    container.appendChild(note);
    setTimeout(() => note.remove(), 1500);
  };
  if (navigator.clipboard) navigator.clipboard.writeText(msg.text).then(done).catch(() => {});
}

// Retry: remove this bot answer and ask the same question again
function retry(chat, botIndex) {
  if (state.loading) return;
  chat.messages.splice(botIndex, 1);
  getAnswer(chat);
}

/* ---------- 10. VOICE INPUT ---------- */
/* Uses the browser's built-in Web Speech API (works in Chrome / Edge).
   No extra AI model needed. The page must run on http://localhost or https. */
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let listening = false;

function toggleVoice() {
  if (!SpeechRecognition) { flashHint(t("noVoice")); return; }
  if (listening) { recognizer.stop(); return; }

  recognizer = new SpeechRecognition();
  recognizer.lang = state.lang === "hi" ? "hi-IN" : "en-IN"; // language of speech
  recognizer.interimResults = true;   // show words while speaking
  recognizer.continuous = false;      // stop after the user pauses

  const baseText = $("input").value;  // keep what was already typed

  recognizer.onstart = () => { listening = true; $("micBtn").classList.add("listening"); flashHint(t("listening"), true); };
  recognizer.onresult = (e) => {
    let spoken = "";
    for (let i = 0; i < e.results.length; i++) spoken += e.results[i][0].transcript;
    $("input").value = (baseText ? baseText + " " : "") + spoken;
    autoGrow();
  };
  recognizer.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") flashHint(t("micDenied"));
  };
  recognizer.onend = () => { listening = false; $("micBtn").classList.remove("listening"); resetHint(); $("input").focus(); };

  recognizer.start();
}

/* ---------- 11. SMALL UI HELPERS & EVENT LISTENERS ---------- */

// Show a temporary message in the line under the input box
let hintTimer;
function flashHint(msg, keep) {
  const h = $("hint");
  h.textContent = msg;
  clearTimeout(hintTimer);
  if (!keep) hintTimer = setTimeout(resetHint, 3500);
}
function resetHint() { $("hint").textContent = t("hint"); }

// Make the textarea grow while typing (up to the CSS max-height)
function autoGrow() {
  const ta = $("input");
  ta.style.height = "auto";
  ta.style.height = ta.scrollHeight + "px";
  updateSendState();
}

// Disable the send button when there's nothing to send or we're waiting
function updateSendState() {
  $("sendBtn").disabled = state.loading || $("input").value.trim() === "";
}

// Apply the selected language to the static parts of the page
function applyLanguage() {
  $("input").placeholder = t("placeholder");
  $("tipText").textContent = t("tip");
  resetHint();
  renderChatList(); renderMessages(); renderSources();
}

// Mobile sidebar open/close
function openSidebar() { $("sidebar").classList.add("open"); $("overlay").classList.add("show"); }
function closeSidebar() { $("sidebar").classList.remove("open"); $("overlay").classList.remove("show"); }

// Show whether we are in demo mode in the header badge
function updateStatusBadge() {
  const badge = $("statusBadge");
  badge.classList.remove("offline");
  $("statusText").textContent = CONFIG.USE_MOCK ? "Demo mode" : "Online";
}

function init() {
  loadState();
  // After a page refresh, open the last chat that was active
  if (!activeChat()) state.activeId = null;

  // --- Keyboard: Enter sends, Shift+Enter makes a new line ---
  $("input").addEventListener("keydown", (e) => {
    // e.isComposing = user is still choosing characters with an IME keyboard (Hindi etc.)
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();          // stop the new line
      sendMessage($("input").value);
    }
  });
  $("input").addEventListener("input", autoGrow);

  // --- Buttons ---
  $("sendBtn").addEventListener("click", () => sendMessage($("input").value));
  $("micBtn").addEventListener("click", toggleVoice);
  $("newChatBtn").addEventListener("click", newChat);
  $("clearHistoryBtn").addEventListener("click", clearHistory);
  $("menuBtn").addEventListener("click", openSidebar);
  $("overlay").addEventListener("click", closeSidebar);

  $("langSelect").addEventListener("change", (e) => { state.lang = e.target.value; applyLanguage(); });

  // --- Settings popup ---
  $("settingsBtn").addEventListener("click", () => {
    $("mockToggle").checked = CONFIG.USE_MOCK;
    $("apiUrlInput").value = CONFIG.API_URL;
    $("settingsDialog").showModal();
  });
  $("settingsDialog").addEventListener("close", () => {
    CONFIG.USE_MOCK = $("mockToggle").checked;
    CONFIG.API_URL = $("apiUrlInput").value.trim() || "/api/chat";
    localStorage.setItem("queryx-config", JSON.stringify({ USE_MOCK: CONFIG.USE_MOCK, API_URL: CONFIG.API_URL }));
    updateStatusBadge();
  });

  updateStatusBadge();
  applyLanguage();
  updateSendState();
}

init();
