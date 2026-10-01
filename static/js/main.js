const $ = (id) => document.getElementById(id);

const UI = {
  en: {
    msg: "Your message, with red flags marked", flags: "Why it looks risky",
    entities: "Details found", advice: "What you should do",
    links: "Links", phones: "Phone numbers", upi: "UPI IDs", amounts: "Amounts",
    none: "Nothing notable found.", noflags: "No red flags detected.", conf: "confidence",
  },
  hinglish: {
    msg: "Aapka message, red flags ke saath", flags: "Ye risky kyun lag raha hai",
    entities: "Mili hui details", advice: "Aapko kya karna chahiye",
    links: "Links", phones: "Phone numbers", upi: "UPI IDs", amounts: "Amounts",
    none: "Kuch khaas nahi mila.", noflags: "Koi red flag nahi mila.", conf: "confidence",
  },
  hi: {
    msg: "आपका मैसेज, ख़तरे के निशान के साथ", flags: "यह जोखिम भरा क्यों लगता है",
    entities: "मिली हुई जानकारी", advice: "आपको क्या करना चाहिए",
    links: "लिंक", phones: "फ़ोन नंबर", upi: "UPI ID", amounts: "रकम",
    none: "कुछ ख़ास नहीं मिला।", noflags: "कोई ख़तरे का निशान नहीं मिला।", conf: "भरोसा",
  },
};

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

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

function render(message, d, lang) {
  const t = UI[lang] || UI.en;

  $("h-msg").textContent = t.msg;
  $("h-flags").textContent = t.flags;
  $("h-entities").textContent = t.entities;
  $("h-advice").textContent = t.advice;

  $("verdict").className = "verdict risk-" + d.risk;
  $("verdict").innerHTML = `
    <h2>${esc(d.verdict)}</h2>
    <p><strong>${esc(d.scam_type.label)}</strong> · ${Math.round(d.scam_type.confidence * 100)}% ${esc(t.conf)}</p>
    <p>${esc(d.summary)}</p>`;

  $("highlighted").innerHTML = highlight(message, d.highlights);

  $("flags").innerHTML = d.red_flags.length
    ? d.red_flags.map((f) => `
        <li class="sev-${f.severity}">
          <strong>${esc(f.label)}</strong><br>${esc(f.explanation)}
          ${f.details && f.details.length ? `<br><small>${f.details.map(esc).join("; ")}</small>` : ""}
        </li>`).join("")
    : `<li>${esc(t.noflags)}</li>`;

  const e = d.entities, parts = [];
  if (e.urls.length) parts.push(t.links + ": " + e.urls.join(", "));
  if (e.phones.length) parts.push(t.phones + ": " + e.phones.join(", "));
  if (e.upi_ids.length) parts.push(t.upi + ": " + e.upi_ids.join(", "));
  if (e.amounts.length) parts.push(t.amounts + ": " + e.amounts.join(", "));
  $("entities").textContent = parts.length ? parts.join("  |  ") : t.none;

  $("advice").innerHTML = d.advice.map((a) => `<li>${esc(a)}</li>`).join("");
  $("result").classList.remove("hidden");
}

async function analyze() {
  const message = $("message").value.trim();
  $("error").classList.add("hidden");
  if (!message) return showError("Please paste a message first.");

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

$("analyzeBtn").addEventListener("click", analyze);
$("clearBtn").addEventListener("click", () => {
  $("message").value = "";
  $("result").classList.add("hidden");
  $("error").classList.add("hidden");
});
document.querySelectorAll(".chip").forEach((b) =>
  b.addEventListener("click", () => { $("message").value = b.dataset.sample; })
);