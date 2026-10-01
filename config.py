from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

RULES_PATH = BASE_DIR / "data" / "rules" / "scam_patterns.json"
HINDI_PATH = BASE_DIR / "data" / "rules" / "translations_hi.json"
DATASET_CSV = BASE_DIR / "data" / "processed" / "dataset.csv"
BASELINE_MODEL_PATH = BASE_DIR / "models" / "baseline" / "model.joblib"

CONFIDENCE_THRESHOLD = 0.5   # below this, fall back to rule-based result
MAX_MESSAGE_LENGTH = 2000