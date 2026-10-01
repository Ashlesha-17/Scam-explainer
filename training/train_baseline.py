import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

import config
from nlp.preprocess import preprocess

df = pd.read_csv(config.DATASET_CSV)  # columns: text,label
df["clean"] = df["text"].astype(str).map(preprocess)

X_train, X_test, y_train, y_test = train_test_split(
    df["clean"], df["label"], test_size=0.2, stratify=df["label"], random_state=42
)

# char n-grams make the model robust to Hinglish spelling variations
features = FeatureUnion([
    ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
    ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
])

model = Pipeline([
    ("features", features),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
model.fit(X_train, y_train)

pred = model.predict(X_test)
print(classification_report(y_test, pred))
print(confusion_matrix(y_test, pred, labels=model.classes_))

config.BASELINE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, config.BASELINE_MODEL_PATH)
print("Saved model to", config.BASELINE_MODEL_PATH)