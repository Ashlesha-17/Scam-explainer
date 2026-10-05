from nlp.classifier import ScamClassifier
from nlp.extractor import extract_entities
from nlp.red_flags import (
    LANG_SUFFIX, SEVERITY_WEIGHT, find_red_flags, load_rules, norm_lang, pick,
)

_classifier = ScamClassifier()

GENERIC_ADVICE = {
    "en": [
        "Never share your OTP, UPI PIN, CVV or password with anyone. Banks never ask for them.",
        "Don't click links in messages. Open your bank's official app or website yourself.",
        "If money is lost, call 1930 or report at cybercrime.gov.in immediately.",
    ],
    "hinglish": [
        "OTP, UPI PIN, CVV ya password kisi ko mat batao. Bank kabhi nahi maangta.",
        "Message ke link par click mat karo. Bank ki official app ya website khud kholo.",
        "Paise chale gaye to turant 1930 par call karo ya cybercrime.gov.in par report karo.",
    ],
    "hi": [
        "OTP, UPI PIN, CVV या पासवर्ड किसी को न बताएँ। बैंक कभी नहीं माँगता।",
        "मैसेज के लिंक पर क्लिक न करें। बैंक की आधिकारिक ऐप या वेबसाइट खुद खोलें।",
        "पैसे कट गए हों तो तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर रिपोर्ट करें।",
    ],
}

VERDICTS = {
    "high": {"en": "High risk: this is very likely a scam",
             "hinglish": "High risk: ye bahut zyada chance scam hai",
             "hi": "ज़्यादा ख़तरा: यह लगभग पक्का स्कैम है"},
    "medium": {"en": "Suspicious: be careful",
               "hinglish": "Shak wala message: savdhaan raho",
               "hi": "संदिग्ध मैसेज: सावधान रहें"},
    "low": {"en": "Looks safe, but never share OTP or PIN",
            "hinglish": "Safe lag raha hai, phir bhi OTP ya PIN kabhi share mat karo",
            "hi": "सुरक्षित लगता है, फिर भी OTP या PIN कभी साझा न करें"},
}


def _risk(pred: dict, flags: list):
    score = sum(SEVERITY_WEIGHT[f["severity"]] for f in flags)
    if pred["label"] != "safe":
        score += round(4 * pred["confidence"])
    if score >= 7:
        return "high", score
    if score >= 4:
        return "medium", score
    return "low", score


def _highlights(flags: list) -> list:
    spans = [
        (m["start"], m["end"], f["severity"], f["label"])
        for f in flags for m in f["matches"]
    ]
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    out, last_end = [], -1
    for start, end, sev, label in spans:
        if start >= last_end:  # drop overlapping spans
            out.append({"start": start, "end": end, "severity": sev, "label": label})
            last_end = end
    return out


def analyze(text: str, lang: str = "en") -> dict:
    lang = norm_lang(lang)
    types = load_rules()["scam_types"]

    entities = extract_entities(text)
    flags = find_red_flags(text, entities, lang)
    pred = _classifier.predict(text)
    risk, score = _risk(pred, flags)

    spec = types.get(pred["label"], types["safe"])
    show_type = not (pred["label"] == "safe" and risk == "low")
    summary = pick(spec if show_type else types["safe"], "description", lang)
    type_advice = spec.get("advice" + LANG_SUFFIX[lang]) or spec.get("advice", [])
    advice = (type_advice if show_type else []) + GENERIC_ADVICE[lang]

    return {
        "verdict": VERDICTS[risk][lang],
        "risk": risk,
        "score": score,
        "scam_type": {
            "id": pred["label"],
            "label": pick(spec, "label", lang),
            "confidence": round(pred["confidence"], 2),
            "source": pred["source"],
        },
        "summary": summary,
        "red_flags": [
            {
                "id": f["id"],
                "label": f["label"],
                "explanation": f["explanation"],
                "severity": f["severity"],
                "examples": [m["text"] for m in f["matches"]][:3],
                "details": f.get("details", []),
            }
            for f in flags
        ],
        "entities": {k: [e["value"] for e in v] for k, v in entities.items()},
        "advice": advice,
        "advice_specific": type_advice if show_type else [],
        "advice_general": GENERIC_ADVICE[lang],
        "highlights": _highlights(flags),
    }