"""
PhishGuard — Comparative Model Evaluation
Evaluates XGBoost vs Random Forest vs SVM vs Logistic Regression
and generates a comparison report.
"""

import os
import sys
import json
import time
import numpy as np
import joblib
from pathlib import Path

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score
)
import xgboost as xgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "models" / "Traditional_ML"))
from feature_extraction import FeatureExtractor

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def load_data(filepath):
    extractor = FeatureExtractor()
    extractor.load_from_file(filepath)
    return extractor.get_handcrafted(), extractor.get_labels()


def evaluate_model(name, model, X_train, y_train, X_test, y_test):
    """Train and evaluate a single model."""
    print(f"\n[PhishGuard] Training {name}...")
    start = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start

    y_pred = model.predict(X_test)

    # Get probabilities if available
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
    elif hasattr(model, "decision_function"):
        y_scores = model.decision_function(X_test)
        auc = roc_auc_score(y_test, y_scores)
    else:
        auc = 0.0

    metrics = {
        "model": name,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1_score": round(f1_score(y_test, y_pred), 4),
        "auc_roc": round(auc, 4),
        "train_time": round(train_time, 2),
    }
    print(f"  → Accuracy: {metrics['accuracy']}, F1: {metrics['f1_score']}, AUC: {metrics['auc_roc']}")
    return metrics


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    train_path = PROJECT_ROOT / "dataset" / "train" / "small_train.txt"
    test_path = PROJECT_ROOT / "dataset" / "test" / "small_test.txt"
    if not train_path.exists():
        train_path = PROJECT_ROOT / "dataset" / "train" / "train.txt"
    if not test_path.exists():
        test_path = PROJECT_ROOT / "dataset" / "test" / "test.txt"

    X_train, y_train = load_data(str(train_path))
    X_test, y_test = load_data(str(test_path))

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = {
        "XGBoost": xgb.XGBClassifier(
            n_estimators=400, max_depth=7, learning_rate=0.1,
            objective="binary:logistic", eval_metric="logloss",
            use_label_encoder=False, random_state=42, tree_method="hist",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=15, random_state=42, n_jobs=-1
        ),
        "SVM": SVC(
            kernel="rbf", C=10, gamma="scale", probability=True, random_state=42
        ),
        "Logistic Regression": LogisticRegression(
            max_iter=1000, C=1.0, random_state=42
        ),
    }

    results = []
    for name, model in models.items():
        metrics = evaluate_model(name, model, X_train_s, y_train, X_test_s, y_test)
        results.append(metrics)

    # Save comparison report
    with open(ARTIFACTS_DIR / "model_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    # Generate comparison bar chart
    names = [r["model"] for r in results]
    metrics_to_plot = ["accuracy", "precision", "recall", "f1_score", "auc_roc"]
    x = np.arange(len(names))
    width = 0.15

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    for i, metric in enumerate(metrics_to_plot):
        vals = [r[metric] for r in results]
        ax.bar(x + i * width, vals, width, label=metric.replace("_", " ").title(), color=colors[i])

    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(names)
    ax.set_ylim(0.8, 1.01)
    ax.set_ylabel("Score")
    ax.set_title("PhishGuard — Model Comparison")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "model_comparison.png", dpi=150)
    plt.close(fig)

    # Print summary table
    print(f"\n{'='*70}")
    print(f"{'Model':<20} {'Acc':>8} {'Prec':>8} {'Recall':>8} {'F1':>8} {'AUC':>8}")
    print(f"{'='*70}")
    for r in results:
        print(f"{r['model']:<20} {r['accuracy']:>8.4f} {r['precision']:>8.4f} "
              f"{r['recall']:>8.4f} {r['f1_score']:>8.4f} {r['auc_roc']:>8.4f}")
    print(f"{'='*70}")

    print(f"\n[PhishGuard] Comparison saved to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
