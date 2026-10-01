import re
from urllib.parse import urlparse

from nlp.preprocess import URL_RE, PHONE_RE

UPI_HANDLES = {
    "okaxis", "oksbi", "okhdfcbank", "okicici", "ybl", "ibl", "axl", "paytm", "upi",
    "apl", "sbi", "hdfcbank", "icici", "axisbank", "kotak", "pnb", "fbl", "waicici",
    "airtel", "jio", "postbank", "idfcbank", "yesbank", "barodampay",
}
UPI_RE = re.compile(r"(?<![\w.])[\w.\-]{2,256}@([a-z]{2,20})\b", re.I)
AMOUNT_RE = re.compile(r"(?:₹|rs\.?|inr|rupees?)\s?([\d,]+(?:\.\d+)?)", re.I)

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "is.gd"}
SUSPICIOUS_TLDS = (".xyz", ".top", ".click", ".link", ".online", ".site", ".info", ".buzz", ".vip")
OFFICIAL_DOMAINS = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "sbi.bank.in"],
    "hdfc": ["hdfcbank.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "kotak": ["kotak.com"],
    "pnb": ["pnbindia.in"],
    "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"],
    "npci": ["npci.org.in"],
}


def _host(url: str) -> str:
    u = url if re.match(r"https?://", url, re.I) else "http://" + url
    return (urlparse(u).hostname or "").lower()


def analyze_url(url: str) -> list:
    """Return a list of reasons why a URL looks risky (empty list = nothing odd found)."""
    host = _host(url)
    reasons = []
    if host in SHORTENERS:
        reasons.append("shortened link hides the real destination")
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        reasons.append("uses a raw IP address instead of a domain name")
    if url.lower().startswith("http://"):
        reasons.append("not a secure (https) connection")
    if host.endswith(SUSPICIOUS_TLDS):
        reasons.append("uses a domain ending commonly seen in scam sites")
    for brand, domains in OFFICIAL_DOMAINS.items():
        if brand in host and not any(host == d or host.endswith("." + d) for d in domains):
            reasons.append(f"mentions '{brand.upper()}' but is not an official {brand.upper()} domain")
            break
    return reasons


def extract_entities(text: str) -> dict:
    urls = []
    for m in URL_RE.finditer(text):
        raw = m.group().rstrip(".,;:!?)\"'")
        urls.append({
            "value": raw,
            "start": m.start(),
            "end": m.start() + len(raw),
            "reasons": analyze_url(raw),
        })

    phones = [{"value": m.group().strip(), "start": m.start(), "end": m.end()}
              for m in PHONE_RE.finditer(text)]

    upi_ids = [{"value": m.group(), "start": m.start(), "end": m.end()}
               for m in UPI_RE.finditer(text) if m.group(1).lower() in UPI_HANDLES]

    amounts = [{"value": m.group().strip(), "start": m.start(), "end": m.end()}
               for m in AMOUNT_RE.finditer(text)]

    return {"urls": urls, "phones": phones, "upi_ids": upi_ids, "amounts": amounts}