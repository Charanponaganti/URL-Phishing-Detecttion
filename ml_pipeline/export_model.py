"""
PhishGuard — Model Export Utility
Exports the trained model with metadata for production deployment.
"""

import json
import joblib
from pathlib import Path
from datetime import datetime

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def generate_model_card():
    """Generate a model card document from saved metrics."""
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    if not metrics_path.exists():
        print("[PhishGuard] No metrics.json found. Run train_xgboost.py first.")
        return

    metrics = json.loads(metrics_path.read_text())

    card = f"""# PhishGuard — Model Card

## Model Details
- **Model Type**: {metrics.get('model', 'XGBoost')}
- **Task**: Binary classification (Phishing vs Legitimate URL)
- **Framework**: XGBoost + scikit-learn
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Metrics
| Metric    | Score  |
|-----------|--------|
| Accuracy  | {metrics['accuracy']:.4f} |
| Precision | {metrics['precision']:.4f} |
| Recall    | {metrics['recall']:.4f} |
| F1 Score  | {metrics['f1_score']:.4f} |
| AUC-ROC   | {metrics['auc_roc']:.4f} |

## Training Details
- **Training Time**: {metrics['train_time_seconds']}s
- **Features**: {metrics['n_features']} hand-crafted lexical features
- **Feature List**: {', '.join(metrics['feature_names'])}

## Files
- `xgboost_model.joblib` — Serialized trained model
- `feature_scaler.joblib` — StandardScaler for feature normalization
- `metrics.json` — Detailed evaluation metrics
- `confusion_matrix.png` — Confusion matrix visualization
- `roc_curve.png` — ROC curve plot
- `feature_importance.png` — Feature importance bar chart

## Usage
```python
import joblib
model = joblib.load("ml_pipeline/artifacts/xgboost_model.joblib")
scaler = joblib.load("ml_pipeline/artifacts/feature_scaler.joblib")
features_scaled = scaler.transform(features.reshape(1, -1))
prediction = model.predict(features_scaled)
probability = model.predict_proba(features_scaled)[:, 1]
```

## Limitations
- Trained on lexical features only (no content or network features)
- May not detect zero-day phishing campaigns with novel URL patterns
- Performance depends on feature distribution matching training data
"""
    card_path = ARTIFACTS_DIR / "MODEL_CARD.md"
    card_path.write_text(card)
    print(f"[PhishGuard] Model card saved to {card_path}")


if __name__ == "__main__":
    generate_model_card()
