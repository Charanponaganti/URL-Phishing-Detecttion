# PhishGuard — Model Card

## Model Details
- **Model Type**: XGBoost
- **Task**: Binary classification (Phishing vs Legitimate URL)
- **Framework**: XGBoost + scikit-learn
- **Export Date**: 2026-05-10 23:21:35

## Performance Metrics
| Metric    | Score  |
|-----------|--------|
| Accuracy  | 0.8979 |
| Precision | 0.8979 |
| Recall    | 0.9203 |
| F1 Score  | 0.9090 |
| AUC-ROC   | 0.9660 |

## Training Details
- **Training Time**: 39.42s
- **Features**: 28 hand-crafted lexical features
- **Feature List**: url_length, domain_length, path_length, subdomain_count, path_depth, count_dots, count_hyphens, count_underscores, count_slashes, count_at, count_question, count_equals, count_ampersand, count_percent, count_digits, digit_ratio, letter_ratio, special_char_ratio, url_entropy, domain_entropy, has_ip_address, has_port, has_https, has_http, has_at_symbol, has_double_slash, has_dash_in_domain, is_shortened

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
