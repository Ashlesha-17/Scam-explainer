from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

RULES_PATH = BASE_DIR / "data" / "rules" / "scam_patterns.json"
HINDI_PATH = BASE_DIR / "data" / "rules" / "translations_hi.json"
DATASET_CSV = BASE_DIR / "data" / "processed" / "dataset.csv"
BASELINE_MODEL_PATH = BASE_DIR / "models" / "baseline" / "model.joblib"

CONFIDENCE_THRESHOLD = 0.5   # below this, fall back to rule-based result
MAX_MESSAGE_LENGTH = 2000

# --- OCR (screenshot input) ---
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # ignored if the file doesn't exist
OCR_LANGS = "eng+hin"
OCR_PSM = 4                 # 4 = single column of text, good for chat screenshots (try 6 if results are poor)
OCR_MIN_CONFIDENCE = 55     # below this, show a "hard to read" warning
OCR_MIN_CHARS = 15
MAX_UPLOAD_MB = 5