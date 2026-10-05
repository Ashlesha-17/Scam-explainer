const $ = (id) => document.getElementById(id);

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

const UI = {
  en: {
    msg: "Your message, with red flags marked", flags: "Why it looks risky",
    entities: "Details found", advice: "What you should do",
    doNow: "Do this now", always: "Always remember", lostTitle: "Already clicked or paid?",
    sev: { high: "High", medium: "Medium", low: "Low" },
    links: "Links", phones: "Phone numbers", upi: "UPI IDs", amounts: "Amounts",
    none: "Nothing notable found.", noflags: "No red flags detected.", conf: "confidence",
    upload: "📷 Screenshot", remove: "Remove", reading: "Reading text from the screenshot…",
    ocrDone: "Text read from the screenshot. Check it for mistakes; if you edit anything, press Analyze again.",
    notImage: "Please choose an image file.", tooBig: "Image is too large (max 5 MB).",
    listen: "🔊 Listen", stop: "⏹ Stop",
    noVoice: "No Hindi voice found on this device. Add one in Windows Settings → Time & language → Speech.",
    unsupported: "Read-aloud is not supported in this browser.",
  },
  hinglish: {
    msg: "Aapka message, red flags ke saath", flags: "Ye risky kyun lag raha hai",
    entities: "Mili hui details", advice: "Aapko kya karna chahiye",
    doNow: "Abhi ye karo", always: "Hamesha yaad rakho", lostTitle: "Link click kiya ya paise bhej diye?",
    sev: { high: "High", medium: "Medium", low: "Low" },
    links: "Links", phones: "Phone numbers", upi: "UPI IDs", amounts: "Amounts",
    none: "Kuch khaas nahi mila.", noflags: "Koi red flag nahi mila.", conf: "confidence",
    upload: "📷 Screenshot", remove: "Hatao", reading: "Screenshot se text padha ja raha hai…",
    ocrDone: "Screenshot se text mil gaya. Galtiyan check karo; kuch edit karo to dobara Analyze dabao.",
    notImage: "Koi image file chuno.", tooBig: "Image bahut badi hai (max 5 MB).",
    listen: "🔊 Suno", stop: "⏹ Roko",
    noVoice: "Is device par Hindi voice nahi mili.",
    unsupported: "Is browser me read-aloud support nahi hai.",
  },
  hi: {
    msg: "आपका मैसेज, ख़तरे के निशान के साथ", flags: "यह जोखिम भरा क्यों लगता है",
    entities: "मिली हुई जानकारी", advice: "आपको क्या करना चाहिए",
    doNow: "अभी यह करें", always: "हमेशा याद रखें", lostTitle: "लिंक खोल लिया या पैसे भेज दिए?",
    sev: { high: "ज़्यादा", medium: "मध्यम", low: "कम" },
    links: "लिंक", phones: "फ़ोन नंबर", upi: "UPI ID", amounts: "रकम",
    none: "कुछ ख़ास नहीं मिला।", noflags: "कोई ख़तरे का निशान नहीं मिला।", conf: "भरोसा",
    upload: "📷 स्क्रीनशॉट", remove: "हटाएँ", reading: "स्क्रीनशॉट से टेक्स्ट पढ़ा जा रहा है…",
    ocrDone: "स्क्रीनशॉट से टेक्स्ट पढ़ लिया गया। गलतियाँ जाँच लें; कुछ बदलें तो फिर से Analyze दबाएँ।",
    notImage: "कृपया कोई इमेज फ़ाइल चुनें।", tooBig: "इमेज बहुत बड़ी है (अधिकतम 5 MB)।",
    listen: "🔊 सुनें", stop: "⏹ रोकें",
    noVoice: "इस डिवाइस पर हिंदी आवाज़ नहीं मिली। Windows Settings → Time & language → Speech में हिंदी वॉइस जोड़ें।",
    unsupported: "इस ब्राउज़र में पढ़कर सुनाने की सुविधा नहीं है।",
  },
};
const t = () => UI[$("lang").value] || UI.en;

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Make the emergency number and portal stand out inside advice text
const KEY = /(1930|cybercrime\.gov\.in)/g;
const keyify = (s) => esc(s).replace(KEY, '<strong class="key">$1</strong>');

// Server spans are in Unicode code points (Python). Array.from splits by code point,
// so emojis in the message don't shift the highlights.
function highlight(text, marks) {
  const chars = Array.from(text);
  let out = "", i = 0;
  for (const m of marks) {
    out += esc(chars.slice(i, m.start).join(""));
    out += `<mark class="sev-${m.severity}" title="${esc(m.label)}">${esc(chars.slice(m.start, m.end).join(""))}</mark>`;
    i = m.end;
  }
  return out + esc(chars.slice(i).join(""));
}

function showError(msg) {
  const el = $("error");
  el.textContent = msg;
  el.classList.remove("hidden");
}
const hideError = () => $("error").classList.add("hidden");

function setStatus(msg, warn = false) {
  const el = $("ocrStatus");
  if (!msg) return el.classList.add("hidden");
  el.textContent = msg;
  el.classList.toggle("warn", warn);
  el.classList.remove("hidden");
}

/* ---------------- Screenshot preview (local only, never stored) ---------------- */
let previewUrl = null;

function formatSize(bytes) {
  return bytes < 1048576
    ? Math.max(1, Math.round(bytes / 1024)) + " KB"
    : (bytes / 1048576).toFixed(1) + " MB";
}

function clearPreview() {
  if (previewUrl) URL.revokeObjectURL(previewUrl);   // free the browser memory
  previewUrl = null;
  $("previewImg").removeAttribute("src");
  $("previewLink").removeAttribute("href");
  $("preview").classList.add("hidden");
}

function showPreview(file) {
  clearPreview();
  previewUrl = URL.createObjectURL(file);
  $("previewImg").src = previewUrl;
  $("previewLink").href = previewUrl;                // click the thumbnail to open full size
  $("previewName").textContent = file.name || "screenshot.png";
  $("previewSize").textContent = formatSize(file.size);
  $("preview").classList.remove("hidden");
}

/* ---------------- Read aloud (browser speech synthesis) ---------------- */
const synth = "speechSynthesis" in window ? window.speechSynthesis : null;
const VOICE_LANG = { en: "en-IN", hinglish: "en-IN", hi: "hi-IN" };
let voices = [], lastResult = null, lastLang = "en", speakToken = 0;

function loadVoices() { voices = synth ? synth.getVoices() : []; }
if (synth) {
  loadVoices();
  synth.addEventListener("voiceschanged", loadVoices);
}

function findVoice(tag) {
  const norm = (s) => s.replace("_", "-").toLowerCase();
  const want = norm(tag), base = want.split("-")[0];
  return voices.find((v) => norm(v.lang) === want) || voices.find((v) => norm(v.lang).startsWith(base));
}

function setListening(on) {
  const btn = $("listenBtn"), ui = UI[lastLang] || UI.en;
  btn.textContent = on ? ui.stop : ui.listen;
  btn.dataset.on = on ? "1" : "";
}

function stopSpeaking() {
  speakToken++;                      // invalidates callbacks of the utterances being cancelled
  if (synth) synth.cancel();
  setListening(false);
}

function speechText(d, lang) {
  const stop = lang === "hi" ? "।" : ".";
  const end = (s) => (/[.!?।]$/.test(s.trim()) ? s.trim() : s.trim() + stop);
  return [d.verdict, d.summary, ...d.advice].filter(Boolean).map(end).join(" ");
}

function speakResult() {
  const ui = UI[lastLang] || UI.en;
  if (!synth) { $("ttsNote").textContent = ui.unsupported; return; }
  if ($("listenBtn").dataset.on) return stopSpeaking();
  if (!lastResult) return;

  const tag = VOICE_LANG[lastLang];
  const voice = findVoice(tag);
  if (!voice && lastLang === "hi") { $("ttsNote").textContent = ui.noVoice; return; }
  $("ttsNote").textContent = "";

  const my = ++speakToken;
  synth.cancel();
  // Speak sentence by sentence: Chrome cuts off long utterances
  const parts = speechText(lastResult, lastLang).match(/[^.!?।]+[.!?।]*/g) || [];
  parts.forEach((p, i) => {
    const u = new SpeechSynthesisUtterance(p.trim());
    u.lang = voice ? voice.lang : tag;
    if (voice) u.voice = voice;
    u.rate = 0.95;
    if (i === parts.length - 1) {
      u.onend = u.onerror = () => { if (my === speakToken) setListening(false); };
    }
    synth.speak(u);
  });
  setListening(true);
}

/* ---------------- Rendering ---------------- */
function render(message, d, lang) {
  const ui = UI[lang] || UI.en;

  lastResult = d;
  lastLang = lang;
  stopSpeaking();
  $("ttsNote").textContent = "";
  $("listenBtn").classList.toggle("hidden", !synth);

  // Section headings in the chosen language
  $("h-msg").textContent = ui.msg;
  $("h-flags").textContent = ui.flags;
  $("h-entities").textContent = ui.entities;
  $("h-advice").textContent = ui.advice;
  $("h-now").textContent = ui.doNow;
  $("h-always").textContent = ui.always;

  // Verdict
  $("verdict").className = "verdict risk-" + d.risk;
  $("verdict").innerHTML = `
    <h2>${esc(d.verdict)}</h2>
    <p class="vmeta"><strong>${esc(d.scam_type.label)}</strong><span>${Math.round(d.scam_type.confidence * 100)}% ${esc(ui.conf)}</span></p>
    <p class="vsummary">${esc(d.summary)}</p>`;

  // Message with highlights, plus a legend for the colours actually used
  $("highlighted").innerHTML = highlight(message, d.highlights);
  const sevs = ["high", "medium", "low"].filter((s) => d.highlights.some((h) => h.severity === s));
  $("legend").innerHTML = sevs.map((s) => `<span class="sev-${s}"><i></i>${esc(ui.sev[s])}</span>`).join("");
  $("legend").classList.toggle("hidden", !sevs.length);

  // Red flags with severity pills
  $("flags").innerHTML = d.red_flags.length
    ? d.red_flags.map((f) => `
        <li class="sev-${f.severity}">
          <div class="flag-head">
            <strong>${esc(f.label)}</strong>
            <span class="pill">${esc(ui.sev[f.severity] || f.severity)}</span>
          </div>
          <p>${esc(f.explanation)}</p>
          ${f.details && f.details.length ? `<small>${f.details.map(esc).join("; ")}</small>` : ""}
        </li>`).join("")
    : `<li><p>${esc(ui.noflags)}</p></li>`;

  // Extracted details as tags
  const e = d.entities;
  const rows = [["urls", ui.links], ["phones", ui.phones], ["upi_ids", ui.upi], ["amounts", ui.amounts]]
    .filter(([k]) => e[k].length)
    .map(([k, label]) => `
      <div class="ent-row">
        <span class="ent-label">${esc(label)}</span>
        <div class="ent-vals">${e[k].map((v) => `<span class="tag">${esc(v)}</span>`).join("")}</div>
      </div>`);
  $("entities").innerHTML = rows.length ? rows.join("") : `<p class="muted">${esc(ui.none)}</p>`;

  // What you should do: specific actions, emergency callout, general rules
  const specific = d.advice_specific || [];
  const general = d.advice_general || d.advice || [];
  const lost = general.find((a) => /1930/.test(a));
  const always = general.filter((a) => a !== lost);

  $("adviceNow").innerHTML = specific.map((a) => `<li>${keyify(a)}</li>`).join("");
  $("nowBlock").classList.toggle("hidden", !specific.length);

  $("lost").innerHTML = lost
    ? `<p class="lost-title">${esc(ui.lostTitle)}</p><p>${keyify(lost)}</p>`
    : "";
  $("lost").classList.toggle("hidden", !lost);

  $("adviceAlways").innerHTML = always.map((a) => `<li>${keyify(a)}</li>`).join("");
  $("alwaysBlock").classList.toggle("hidden", !always.length);

  $("result").classList.remove("hidden");
}

/* ---------------- Analyze ---------------- */
async function analyze() {
  const message = $("message").value.trim();
  hideError();
  if (!message) return showError("Please paste a message first.");

  stopSpeaking();
  const btn = $("analyzeBtn");
  btn.disabled = true;
  btn.textContent = "Analyzing...";
  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, lang: $("lang").value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    render(message, data, $("lang").value);
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze";
  }
}

/* ---------------- Screenshot OCR ---------------- */
async function runOcr(file) {
  hideError();
  if (!file.type.startsWith("image/")) return showError(t().notImage);
  if (file.size > MAX_IMAGE_BYTES) return showError(t().tooBig);

  showPreview(file);                                 // show the image straight away

  const up = $("uploadBtn");
  up.disabled = true;
  setStatus(t().reading);
  try {
    const fd = new FormData();
    fd.append("image", file, file.name || "screenshot.png");
    const res = await fetch("/ocr", { method: "POST", body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Could not read the screenshot.");

    $("message").value = data.text;                  // user can correct OCR mistakes here
    setStatus(data.warning || t().ocrDone, Boolean(data.warning));
    await analyze();
  } catch (err) {
    setStatus("");
    showError(err.message);
  } finally {
    up.disabled = false;
  }
}

/* ---------------- Wiring ---------------- */
$("analyzeBtn").addEventListener("click", analyze);
$("listenBtn").addEventListener("click", speakResult);

$("clearBtn").addEventListener("click", () => {
  stopSpeaking();
  $("message").value = "";
  $("result").classList.add("hidden");
  hideError();
  setStatus("");
  clearPreview();
});

$("previewRemove").addEventListener("click", () => {
  clearPreview();
  setStatus("");
});

document.querySelectorAll(".chip").forEach((b) =>
  b.addEventListener("click", () => {
    $("message").value = b.dataset.sample;
    setStatus("");
    clearPreview();                                  // example text is not from the screenshot
  })
);

// Upload button
$("uploadBtn").addEventListener("click", () => $("imageInput").click());
$("imageInput").addEventListener("change", (e) => {
  const file = e.target.files[0];
  e.target.value = "";                               // lets the same file be chosen again
  if (file) runOcr(file);
});

// Paste a screenshot straight into the box (Win + Shift + S, then Ctrl + V)
$("message").addEventListener("paste", (e) => {
  const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
  if (item) {
    e.preventDefault();
    runOcr(item.getAsFile());
  }
});

// Drag and drop an image onto the box
const box = $("message");
const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes("Files");
["dragenter", "dragover"].forEach((ev) =>
  box.addEventListener(ev, (e) => {
    if (hasFiles(e)) { e.preventDefault(); box.classList.add("dragging"); }
  })
);
["dragleave", "drop"].forEach((ev) => box.addEventListener(ev, () => box.classList.remove("dragging")));
box.addEventListener("drop", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file) runOcr(file);
});

// Keep the button labels in the selected language
function applyLabels() {
  $("uploadBtn").textContent = t().upload;
  $("previewRemove").textContent = t().remove;
}
$("lang").addEventListener("change", applyLabels);
applyLabels();