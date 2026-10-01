import re
from pathlib import Path

import joblib

import config
from nlp.preprocess import preprocess
from nlp.red_flags import load_rules


class ScamClassifier:
    """Uses the trained model if it exists, otherwise falls back to keyword rules,
    so the app works from day one."""

    def __init__(self):
        self.model = None
        if Path(config.BASELINE_MODEL_PATH).exists():
            self.model = joblib.load(config.BASELINE_MODEL_PATH)

        types = load_rules()["scam_types"]
        self._kw = {
            t: [re.compile(p, re.I | re.S) for p in spec.get("keywords", [])]
            for t, spec in types.items()
            if spec.get("keywords")
        }

    def _rule_predict(self, text: str) -> dict:
        scores = {t: sum(1 for p in pats if p.search(text)) for t, pats in self._kw.items()}
        best = max(scores, key=scores.get) if scores else "safe"
        if not scores or scores[best] == 0:
            return {"label": "safe", "confidence": 0.6, "source": "rules"}
        return {
            "label": best,
            "confidence": min(0.95, 0.45 + 0.15 * scores[best]),
            "source": "rules",
        }

    def predict(self, text: str) -> dict:
        rule = self._rule_predict(text)
        if self.model is None:
            return rule

        probs = self.model.predict_proba([preprocess(text)])[0]
        i = int(probs.argmax())
        pred = {
            "label": str(self.model.classes_[i]),
            "confidence": float(probs[i]),
            "source": "model",
            "scores": {str(c): round(float(p), 3) for c, p in zip(self.model.classes_, probs)},
        }
        if pred["confidence"] < config.CONFIDENCE_THRESHOLD and rule["label"] != "safe":
            return rule
        return pred