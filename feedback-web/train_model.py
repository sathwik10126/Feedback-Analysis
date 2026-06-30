"""
Train sentiment model on the expanded feedback dataset.
Usage: python train_model.py
"""
import os, pickle, warnings
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "feedback_dataset.csv")
MDIR = os.path.join(BASE, "model")
os.makedirs(MDIR, exist_ok=True)

print("=" * 55)
print("  University Feedback — NLP Sentiment Model Trainer")
print("=" * 55)

# ── Load & inspect ─────────────────────────────────────────────
df = pd.read_csv(DATA).dropna(subset=["text","label"])
df["text"] = df["text"].str.strip().str.lower()
df["label"] = df["label"].astype(int)

print(f"\n📂 Dataset: {len(df)} samples")
for lbl, name in [(1,"Positive"),(0,"Negative"),(2,"Neutral")]:
    n = (df["label"]==lbl).sum()
    print(f"   {name:10s}: {n:3d}  ({n/len(df)*100:.1f}%)")

# ── Split ──────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)
print(f"\n🔀 Train: {len(X_train)}  |  Test: {len(X_test)}")

# ── Vectorizer ─────────────────────────────────────────────────
vectorizer = TfidfVectorizer(
    max_features=8000,
    ngram_range=(1, 3),       # unigrams + bigrams + trigrams
    sublinear_tf=True,        # log scaling
    min_df=1,
    strip_accents="unicode",
    analyzer="word",
)

X_tr = vectorizer.fit_transform(X_train)
X_te = vectorizer.transform(X_test)
print(f"🔧 Vocabulary size: {len(vectorizer.vocabulary_)}")

# ── Train multiple models & pick best ─────────────────────────
candidates = {
    "Logistic Regression": LogisticRegression(C=5.0, max_iter=1000),
    "Linear SVC (calibrated)": CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2000)),
}

print("\n📊 Cross-validation (5-fold):")
best_name, best_score, best_model = None, 0, None
for name, clf in candidates.items():
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X_tr, y_train, cv=cv, scoring="accuracy")
    mean, std = scores.mean(), scores.std()
    print(f"   {name:30s}  acc={mean:.4f} ± {std:.4f}")
    if mean > best_score:
        best_score, best_name, best_model = mean, name, clf

print(f"\n🏆 Best model: {best_name}  (CV acc={best_score:.4f})")

# ── Final fit on full train set ────────────────────────────────
best_model.fit(X_tr, y_train)
y_pred = best_model.predict(X_te)

print(f"\n✅ Test Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
print("\n📋 Classification Report:")
print(classification_report(y_test, y_pred,
      target_names=["Negative(0)","Positive(1)","Neutral(2)"]))

print("🔲 Confusion Matrix (rows=actual, cols=pred):")
cm = confusion_matrix(y_test, y_pred, labels=[0,1,2])
header = f"{'':12s} {'Neg':>6} {'Pos':>6} {'Neu':>6}"
print(header)
for row_lbl, row in zip(["Negative","Positive","Neutral"], cm):
    print(f"  {row_lbl:10s}  {row[0]:6d} {row[1]:6d} {row[2]:6d}")

# ── Save ───────────────────────────────────────────────────────
with open(os.path.join(MDIR,"model.pkl"),      "wb") as f: pickle.dump(best_model,  f)
with open(os.path.join(MDIR,"vectorizer.pkl"), "wb") as f: pickle.dump(vectorizer, f)

print(f"\n💾 Saved → model/model.pkl & model/vectorizer.pkl")
print("=" * 55)