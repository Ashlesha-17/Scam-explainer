import json
import re
from functools import lru_cache
from pathlib import Path

import config

# Hindi/Devanagari uses "मत" and "नहीं" for negation; \b doesn't work reliably around matras
NEGATION_RE = re.compile(
    r"\b(?:do not|don't|dont|never|not to|mat|na|nahi|nahin|kabhi nahi)\b|मत|नहीं|न ",
    re.I,
)
SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}

LANG_SUFFIX = {"en": "", "hinglish": "_hl", "hi": "_hi"}

URL_REASONS_HI = {
    "shortened link hides the real destination": "छोटा किया गया लिंक असली वेबसाइट छिपा देता है",
    "uses a raw IP address instead of a domain name": "डोमेन नाम की जगह सीधे IP एड्रेस का इस्तेमाल",
    "not a secure (https) connection": "सुरक्षित (https) कनेक्शन नहीं है",
    "uses a domain ending commonly seen in scam sites": "ऐसा डोमेन जो अक्सर स्कैम साइटों पर दिखता है",
}
MENTIONS_RE = re.compile(r"mentions '(.+)' but is not an official (.+) domain")


def norm_lang(lang: str) -> str:
    lang = {"hl": "hinglish"}.get(lang, lang)
    return lang if lang in LANG_SUFFIX else "en"


def pick(spec: dict, key: str, lang: str):
    """Return spec[key + language suffix], falling back to English if it's missing."""
    return spec.get(key + LANG_SUFFIX[lang]) or spec.get(key, "")


def translate_reason(reason: str, lang: str) -> str:
    if lang != "hi":
        return reason
    if reason in URL_REASONS_HI:
        return URL_REASONS_HI[reason]
    m = MENTIONS_RE.match(reason)
    if m:
        return f"'{m.group(1)}' का नाम है, पर यह आधिकारिक {m.group(2)} वेबसाइट नहीं है"
    return reason


@lru_cache(maxsize=1)
def load_rules() -> dict:
    with open(config.RULES_PATH, encoding="utf-8") as f:
        rules = json.load(f)

    if Path(config.HINDI_PATH).exists():
        with open(config.HINDI_PATH, encoding="utf-8") as f:
            hi = json.load(f)
        for section in ("scam_types", "red_flags"):
            for rid, extra in hi.get(section, {}).items():
                target = rules[section].get(rid)
                if target is None:
                    continue
                for key, val in extra.items():
                    if key == "patterns_extra":
                        target["patterns"] = target.get("patterns", []) + val
                    elif key == "keywords_extra":
                        target["keywords"] = target.get("keywords", []) + val
                    else:
                        target[key] = val
    return rules


@lru_cache(maxsize=1)
def _compiled() -> dict:
    flags = load_rules()["red_flags"]
    return {
        fid: [re.compile(p, re.I | re.S) for p in spec.get("patterns", [])]
        for fid, spec in flags.items()
    }


def _make(fid, spec, matches, lang):
    return {
        "id": fid,
        "label": pick(spec, "label", lang),
        "explanation": pick(spec, "explanation", lang),
        "severity": spec["severity"],
        "matches": matches,
    }


def find_red_flags(text: str, entities: dict, lang: str = "en") -> list:
    """Find manipulation tactics in the ORIGINAL text (so spans can be highlighted in the UI)."""
    lang = norm_lang(lang)
    rules = load_rules()["red_flags"]
    found = []

    for fid, patterns in _compiled().items():
        spec = rules[fid]
        matches = []
        for pat in patterns:
            for m in pat.finditer(text):
                if spec.get("negation_guard"):
                    # skip "Do NOT share your OTP" / "OTP किसी को न बताएँ" style safety warnings
                    window = text[max(0, m.start() - 20):m.end() + 12]
                    if NEGATION_RE.search(window):
                        continue
                matches.append({"start": m.start(), "end": m.end(), "text": m.group()})
        if matches:
            found.append(_make(fid, spec, matches, lang))

    urls = entities["urls"]
    if urls:
        flag = _make(
            "suspicious_link",
            rules["suspicious_link"],
            [{"start": u["start"], "end": u["end"], "text": u["value"]} for u in urls],
            lang,
        )
        details = sorted({translate_reason(r, lang) for u in urls for r in u["reasons"]})
        flag["severity"] = "high" if details else "medium"
        flag["details"] = details
        found.append(flag)

    return found