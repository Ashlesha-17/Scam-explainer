import re
import unicodedata

URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|\b(?:bit\.ly|tinyurl\.com|t\.co|cutt\.ly|rb\.gy|is\.gd)/\S+",
    re.I,
)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
LONG_NUM_RE = re.compile(r"\d{5,}")
REPEAT_RE = re.compile(r"(.)\1{2,}")
# \u0900-\u097F keeps Devanagari (Hindi/Marathi) words intact
TOKEN_RE = re.compile(r"[\w\u0900-\u097F/]+|[^\w\s]")

# Common Hinglish / SMS-style spelling variants -> one canonical form
NORMALIZE = {
    "kro": "karo", "krdo": "kar do", "krna": "karna", "krlo": "kar lo", "kre": "kare",
    "updt": "update", "updte": "update", "upadte": "update",
    "acc": "account", "acct": "account", "a/c": "account", "accnt": "account",
    "blk": "block", "blck": "block", "bloc": "block", "blocked": "block",
    "verfy": "verify", "vrfy": "verify", "verifiy": "verify",
    "immediatly": "immediately", "immediate": "immediately",
    "pls": "please", "plz": "please", "pleas": "please",
    "hojayega": "ho jayega", "hojaega": "ho jayega", "jaega": "jayega", "jayga": "jayega",
    "bnd": "band", "bandh": "band",
    "adhar": "aadhaar", "aadhar": "aadhaar", "adhaar": "aadhaar",
    "paytym": "paytm", "phonepay": "phonepe", "gpay": "googlepay",
    "nhi": "nahi", "nahin": "nahi", "nai": "nahi",
    "wapas": "wapas", "wapis": "wapas", "vapas": "wapas",
    "paise": "paise", "paisa": "paise", "pese": "paise", "rupaye": "rupees", "rs": "rupees",
    "ghante": "ghanta", "ghantey": "ghanta", "hrs": "hours", "hr": "hours",
    "otp": "otp", "o.t.p": "otp",
}


def preprocess(text: str) -> str:
    """Clean a raw (Hinglish) message into a normalized string for the classifier."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = URL_RE.sub(" urltoken ", text)
    text = PHONE_RE.sub(" phonetoken ", text)
    text = re.sub(r"(?:₹|rs\.?|inr)\s?(?=\d)", " rupees ", text)
    text = LONG_NUM_RE.sub(" numtoken ", text)
    text = REPEAT_RE.sub(r"\1\1", text)
    tokens = TOKEN_RE.findall(text)
    tokens = [NORMALIZE.get(t, t) for t in tokens]
    return " ".join(tokens)