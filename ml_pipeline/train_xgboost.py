"""
PhishGuard — XGBoost Training Pipeline
Trains an XGBoost classifier on hand-crafted URL features,
performs hyperparameter tuning, and exports the serialized model.
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_curve
)
import xgboost as xgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add project root to path so we can import the existing feature extractor
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "models" / "Traditional_ML"))
from feature_extraction import FeatureExtractor, FEATURE_NAMES

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def load_data(filepath: str):
    """Load URL data and extract hand-crafted features."""
    extractor = FeatureExtractor()
    extractor.load_from_file(filepath)
    X = extractor.get_handcrafted()
    y = extractor.get_labels()
    return X, y


def train_xgboost(X_train, y_train, tune=True):
    """Train XGBoost with optional hyperparameter tuning."""
    if tune:
        print("\n[PhishGuard] Running hyperparameter grid search...")
        param_grid = {
            "n_estimators": [200, 400],
            "max_depth": [5, 7, 9],
            "learning_rate": [0.05, 0.1],
            "subsample": [0.8, 1.0],
            "colsample_bytree": [0.8, 1.0],
        }
        base_model = xgb.XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
            tree_method="hist",
        )
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        grid = GridSearchCV(
            base_model, param_grid, cv=cv, scoring="accuracy",
            n_jobs=-1, verbose=1, refit=True
        )
        grid.fit(X_train, y_train)
        print(f"[PhishGuard] Best params: {grid.best_params_}")
        print(f"[PhishGuard] Best CV accuracy: {grid.best_score_:.4f}")
        return grid.best_estimator_, grid.best_params_
    else:
        model = xgb.XGBClassifier(
            n_estimators=400, max_depth=7, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            objective="binary:logistic", eval_metric="logloss",
            use_label_encoder=False, random_state=42, tree_method="hist",
        )
        model.fit(X_train, y_train)
        return model, model.get_params()


def evaluate_and_save(model, scaler, X_test, y_test, params, duration):
    """Evaluate model and save all artifacts."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print(f"\n{'='*50}")
    print(f"  PhishGuard XGBoost — Test Results")
    print(f"{'='*50}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  AUC-ROC:   {auc:.4f}")
    print(f"  Train Time: {duration:.2f}s")
    print(f"{'='*50}\n")

    # Classification report
    report = classification_report(y_test, y_pred, target_names=["Phishing", "Legitimate"])
    print(report)
    with open(ARTIFACTS_DIR / "classification_report.txt", "w") as f:
        f.write(report)

    # Save model + scaler
    joblib.dump(model, ARTIFACTS_DIR / "xgboost_model.joblib")
    joblib.dump(scaler, ARTIFACTS_DIR / "feature_scaler.joblib")
    print(f"[PhishGuard] Model saved to {ARTIFACTS_DIR / 'xgboost_model.joblib'}")

    # Save metrics JSON
    metrics = {
        "model": "XGBoost",
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "auc_roc": round(auc, 4),
        "train_time_seconds": round(duration, 2),
        "best_params": params,
        "feature_names": FEATURE_NAMES,
        "n_features": len(FEATURE_NAMES),
        "n_train_samples": int(model.n_features_in_) if hasattr(model, "n_features_in_") else None,
    }
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Confusion matrix plot
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Phishing", "Legitimate"])
    ax.set_yticklabels(["Phishing", "Legitimate"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("PhishGuard XGBoost — Confusion Matrix")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=16)
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#2563eb", lw=2, label=f"XGBoost (AUC = {auc:.4f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("PhishGuard XGBoost — ROC Curve")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "roc_curve.png", dpi=150)
    plt.close(fig)

    # Feature importance
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    top_n = min(20, len(FEATURE_NAMES))
    ax.barh(range(top_n), importances[indices[:top_n]], color="#2563eb")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([FEATURE_NAMES[i] for i in indices[:top_n]])
    ax.invert_yaxis()
    ax.set_xlabel("Feature Importance")
    ax.set_title("PhishGuard — Top Feature Importances")
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)

    return metrics


def main():
    print("[PhishGuard] Loading training data...")
    train_path = PROJECT_ROOT / "dataset" / "train" / "train.txt"
    test_path = PROJECT_ROOT / "dataset" / "test" / "test.txt"

    # Fall back to small dataset if full versions don't exist
    if not train_path.exists():
        train_path = PROJECT_ROOT / "dataset" / "train" / "small_train.txt"
    if not test_path.exists():
        test_path = PROJECT_ROOT / "dataset" / "test" / "small_test.txt"

    X_train, y_train = load_data(str(train_path))
    X_test, y_test = load_data(str(test_path))

    print(f"[PhishGuard] Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"[PhishGuard] Train class dist: phishing={sum(y_train==0)}, legit={sum(y_train==1)}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train
    start = time.time()
    model, params = train_xgboost(X_train_scaled, y_train, tune=False)
    duration = time.time() - start

    # Evaluate & save
    evaluate_and_save(model, scaler, X_test_scaled, y_test, params, duration)
    print("[PhishGuard] Pipeline complete!")


if __name__ == "__main__":
    main()
