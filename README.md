# PhishGuard 🛡️

### An ML-Powered Phishing URL Detection System with Cyber Threat Intelligence Integration

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0+-9b51e0.svg)](https://vitejs.dev/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**PhishGuard** is an end-to-end, enterprise-grade phishing detection and cyber threat intelligence orchestration system. Built as a comprehensive modernization and production-ready expansion of the **DEPHIDES (Deep Learning Based Phishing URL Detection System)** research framework, PhishGuard transitions high-precision deep sequence modeling into an active, low-latency browser protection suite. 

The system operates as a real-time **Chrome MV3 Browser Extension** backed by a high-performance **FastAPI REST API** backend and a responsive **React (Vite) Analyst Dashboard**. It bridges statistical machine learning classification, structural heuristics, live OSINT Threat Intelligence (CTI), active DNS/WHOIS forensics, and deobfuscation algorithms into a unified threat score.

---

## 🏗️ Technical Architecture & Workflow

```
┌──────────────────┐      HTTPS POST      ┌─────────────────────────────────┐
│ Chrome Extension │ ───────────────────▶ │         FastAPI Backend         │
│ (Active Scanning)│                      │         (Uvicorn Host)          │
│                  │ ◀─────────────────── │                                 │
│  • Auto-scan     │   JSON Scan Schema   │   ┌─────────────────────────┐   │
│  • Risk Badge    │                      │   │  URL Deobfuscation      │   │
│  • Popup Card    │                      │   ├─────────────────────────┤   │
│                  │                      │   │  XGBoost Classifier     │   │
└──────────────────┘                      │   ├─────────────────────────┤   │
                                          │   │  VirusTotal & URLhaus   │   │
┌──────────────────┐                      │   ├─────────────────────────┤   │
│React Dashboard UI│                      │   │  DNS & WHOIS Forensics  │   │
│ (Analyst Portal) │                      │   ├─────────────────────────┤   │
│                  │                      │   │  Typosquatting Check    │   │
│  • Scan History  │                      │   └─────────────────────────┘   │
│  • Recharts Visuals                     └─────────────────────────────────┘
│  • IoC Exports   │                                       │
│  • Live Auditing │                                       ▼
└──────────────────┘                            ┌────────────────────┐
                                                │ SQLite DB Archives │
                                                │  (phishguard.db)   │
                                                └────────────────────┘
```

When a URL is scanned (either captured dynamically by the extension service worker or entered manually by an analyst), PhishGuard triggers five specialized evaluation engines in parallel:

1. **URL Deobfuscation & Normalization**:
   - Decodes multi-stage percent-encoding (e.g., `%20`), punycode (internationalized domain names), and decimal/hexadecimal/octal IP address representations.
   - Detects and resolves popular URL shorteners (e.g., `bit.ly`, `tinyurl.com`, `t.co`) to evaluate the ultimate landing page.
2. **Typosquatting & Homoglyph Detector**:
   - Calculates Levenshtein distances and structural similarities against a built-in dictionary of high-profile target brands (Tranco Top 1000).
   - Identifies IDN Homograph Attacks (e.g., Cyrillic characters substituted for visually identical Latin characters).
3. **DNS & WHOIS Forensics Engine**:
   - Dynamically resolves active DNS records (`A`, `MX`, `NS`) utilizing `dnspython`.
   - Performs asynchronous WHOIS queries via `python-whois` to analyze registration parameters.
   - Flags **Newly Registered Domains (NRDs)** (domain age < 30 days), which are statistically linked to temporary phishing campaigns.
4. **Cyber Threat Intelligence (CTI) Orchestration**:
   - Queries the **VirusTotal API** for multi-engine antivirus classifications.
   - Integrates with the **URLhaus API** to cross-reference active malware and credential-harvesting distribution points.
   - Designed to degrade gracefully if API keys are absent or rate limits are reached.
5. **XGBoost Classifier Engine**:
   - Extracts 28 hand-crafted structural, lexical, and statistical features (e.g., Shannon entropy, subdomain depths, digit-to-letter ratios).
   - Standardizes inputs using a pre-saved `StandardScaler` and runs real-time binary inference using a serialized XGBoost model.

---

## 📈 ML Pipeline vs. Deep Learning (DEPHIDES Legacy)

PhishGuard maintains full backwards compatibility with the original DEPHIDES deep learning models, while incorporating a streamlined XGBoost classifier for fast, real-time protection.

| Model / Architecture | Primary Technology | Inference Latency | Computing Footprint | Target Environment | Key Benefit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost (PhishGuard)** | Scikit-Learn, XGBoost | **< 1.0 ms** | Ultra-lightweight CPU | Real-time Extension / REST API | High throughput, sub-millisecond execution, high interpretability. |
| **CNN Complex** | TensorFlow / Keras | ~22.0 ms | Moderate GPU / CPU | Forensic Batch Scanning | Processes URLs as raw character sequences; resilient to unseen zero-day structures. |
| **BRNN Complex** | TensorFlow / Keras | ~45.0 ms | Heavy GPU / CPU | Deep Offline Threat Hunting | Captures bidirectional chronological sequence context in long URLs. |
| **Self-Attention** | TensorFlow / Keras | ~30.0 ms | Moderate GPU / CPU | Deep Offline Threat Hunting | Highlights exact suspicious slices and character strings in the URL path. |

---

## 📁 Project Structure

```
PhishGuard/
├── backend/                     # FastAPI REST API Backend
│   ├── app/
│   │   ├── main.py              # Application entrypoint & CORS middleware
│   │   ├── config.py            # Settings and Pydantic-settings environment loading
│   │   ├── models/
│   │   │   ├── database.py      # SQLite / aiosqlite asynchronous schema manager
│   │   │   └── schemas.py       # Pydantic request/response validation schemas
│   │   ├── routers/
│   │   │   ├── scan.py          # /api/scan endpoint logic & aggregate risk score computation
│   │   │   ├── history.py       # paginated history and summary telemetry endpoints
│   │   │   └── report.py        # IoC bulk export (JSON / CSV formatters)
│   │   └── services/
│   │       ├── cti_lookup.py    # VirusTotal & URLhaus lookup connectors
│   │       ├── dns_whois.py     # python-whois registration queries and NRD flags
│   │       ├── feature_extractor.py # Hand-crafted feature extractor for live ML inference
│   │       ├── ml_predictor.py  # SerDe model wrapper and fallback heuristics
│   │       ├── obfuscation.py   # Percent decoder, punycode normalizer, and shortener resolver
│   │       └── typosquatting.py # Levenshtein & homoglyph spoofing engine
│   ├── requirements.txt         # Backend-specific package constraints
│   ├── run.py                   # Development server boot script
│   └── phishguard.db            # Local SQLite database (auto-generated)
├── ml_pipeline/                 # XGBoost training & evaluation sandbox
│   ├── train_xgboost.py         # Grid search trainer, pipeline serializer, and plotter
│   ├── evaluate_models.py       # Cross-model verification and comparison script
│   ├── export_model.py          # Model card generator and metadata writer
│   └── artifacts/               # Serialized model bins (.joblib) and metrics plots
├── dashboard/                   # React Analyst Dashboard (Vite SPA)
│   ├── src/
│   │   ├── components/          # ScanForm, ThreatReport, RiskGauge, HistoryTable, StatsPanel
│   │   └── services/api.js      # REST client integrations
│   ├── package.json             # Node dependencies (React 18, Tailwind, Recharts)
│   └── vite.config.js           # Vite server settings
├── extension/                   # Chrome MV3 Browser Extension
│   ├── manifest.json            # Extension metadata and permissions
│   ├── background.js            # Active tab listener and background service worker
│   ├── popup.html/js/css        # Threat indicator drawer popup
│   └── icons/                   # Extension icons (Safe, Warn, Danger badge images)
├── models/                      # DEPHIDES Deep Learning models (CNN, RNN, BRNN, ANN)
│   └── Traditional_ML/          # Legacy traditional ML feature extractions
├── dataset/                     # Training & test matrices
├── evaluate.py                  # Deep learning training and evaluation CLI
├── requirements.txt             # Unified Python dependencies
└── .env.example                 # Environment configuration template
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: Version `3.9` or higher
- **Node.js**: Version `16.0` or higher
- **Browser**: Google Chrome or any Chromium-based browser (Brave, Edge, Opera)

### 1. Repository Setup & Dependencies
First, open your terminal, set up a virtual environment, and install the required dependencies:

```bash
# Clone the repository
git clone https://github.com/charan-435/URL-Phishing-Detection.git
cd URL-Phishing-Detection

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the unified Python packages
pip install -r requirements.txt
```

### 2. Environment Configuration
PhishGuard supports live threat database queries. Configure the environment variables to activate these:

```bash
# Copy the template environment file
cp .env.example .env
```
Open the newly created `.env` file in your editor and add your **VirusTotal API Key**:
```env
# VirusTotal API Key (Free tier allows 4 requests/min)
VIRUSTOTAL_API_KEY=your_actual_virustotal_api_key_here
URLHAUS_ENABLED=true
DEBUG=true
```

### 3. Train the XGBoost Classifier
Extract features from the dataset and train the optimized XGBoost classifier model:

```bash
python ml_pipeline/train_xgboost.py
```
*This command runs hyperparameter checks, scales the training data, serializes the models into `ml_pipeline/artifacts/`, and saves visual metrics (Confusion Matrix, ROC Curve, and Feature Importance).*

### 4. Launch the FastAPI Backend
Start the high-performance local FastAPI REST server:

```bash
cd backend
pip install -r requirements.txt
python run.py
```
The server will boot up and be accessible at:
- **API Server**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Start the React Dashboard
Open a new terminal window, navigate to the dashboard directory, install Node packages, and start the development server:

```bash
cd dashboard
npm install
npm run dev
```
The React analyst console will compile and open at:
- **Analyst Portal**: [http://localhost:5173](http://localhost:5173)

### 6. Install the Chrome MV3 Extension
1. Open Google Chrome and navigate to `chrome://extensions/`
2. In the top-right corner, toggle **Developer mode** to **ON**.
3. In the top-left, click **Load unpacked**.
4. Select the `extension/` folder inside the project root.
5. The PhishGuard shield icon will appear in your extensions list. It will now automatically inspect tabs and display real-time safety badges!

---

## 📊 API Documentation & Schema

### `POST` — `/api/scan`
Executes a full multi-engine threat analysis pipeline on a URL.

#### Request Payload
```json
{
  "url": "http://paypal-security.update-verification.com/login"
}
```

#### Response Example (`200 OK`)
```json
{
  "scan_id": "cf3a8b2c",
  "url": "http://paypal-security.update-verification.com/login",
  "timestamp": "2026-05-29T16:45:12.894Z",
  "risk_score": 85,
  "risk_level": "malicious",
  "ml_prediction": {
    "label": "phishing",
    "confidence": 0.985,
    "risk_score": 75,
    "feature_importances": {
      "url_length": 0.045,
      "shannon_entropy": 0.082,
      "special_char_ratio": 0.061,
      "subdomain_depth": 0.038
    }
  },
  "cti_result": {
    "virustotal": {
      "status": "found",
      "malicious": 6,
      "suspicious": 1,
      "harmless": 68
    },
    "urlhaus": {
      "status": "found",
      "threat": "phishing_credentials",
      "reporter": "abuse_ch"
    },
    "sources_checked": 2
  },
  "dns_whois": {
    "dns_records": {
      "A": ["198.51.100.42"],
      "MX": ["mail.update-verification.com"]
    },
    "whois_info": {
      "registrar": "NameCheap Inc.",
      "creation_date": "2026-05-20"
    },
    "domain_age_days": 9,
    "registrar": "NameCheap Inc.",
    "newly_registered": true
  },
  "obfuscation": {
    "original_url": "http://paypal-security.update-verification.com/login",
    "decoded_url": "http://paypal-security.update-verification.com/login",
    "techniques_detected": [],
    "is_shortened": false,
    "resolved_url": null
  },
  "typosquatting": {
    "is_typosquatting": true,
    "similar_domains": [
      {
        "domain": "paypal.com",
        "similarity": 0.88,
        "rank": 4
      }
    ],
    "closest_match": "paypal.com"
  },
  "summary": "⚠️ HIGH RISK: This URL is likely malicious. ML model classifies as phishing (98.5% confidence). VirusTotal: 6 engines flagged this URL. URLhaus: Known threat — phishing_credentials. Possible typosquatting of: paypal.com."
}
```

### Other Core Endpoints
- `GET` — `/api/history` : Retrieve the paginated audit logs of scanned URLs.
- `GET` — `/api/history/stats` : Returns aggregate numbers (safe, suspicious, malicious ratios, average risk score, scan velocity).
- `GET` — `/api/report/export?format=csv|json` : Exports IOC lists for SOC integration.
- `GET` — `/health` : API server health verification.

---

## 🧠 Core Deep Learning (DEPHIDES) Modeling
The underlying deep learning models utilize character-level sequence modeling to recognize malicious structural patterns without requiring explicit feature engineering.

To train or evaluate any of the five deep learning neural network architectures, execute the `evaluate.py` script:

```bash
# Evaluate the 17-layer CNN Complex model
python evaluate.py --model cnn_complex --sequence_length 512 --epochs 10

# Train the 7-layer stacked BRNN Complex model
python evaluate.py --model brnn_complex --sequence_length 512 --epochs 5

# Evaluate the Self-Attention model
python evaluate.py --model att_complex --sequence_length 512 --epochs 10
```

---

*Built on the DEPHIDES deep learning phishing detection framework, extended with live cyber threat intelligence orchestration and active browser protection.*