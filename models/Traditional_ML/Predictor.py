import joblib
import numpy as np
from urllib.parse import urlparse
import re
from feature_extraction import FeatureExtractor

#using the same feature extractor
extractor = FeatureExtractor()
def extract_features(url):
    features = []

    features = extractor._extract_one(url)

    

    return features


#using the same scaler

scaler = joblib.load(r"output_data\feature_scaler.joblib")

#models

models = {
    "RF": joblib.load(r"output_data\RF\RF_model.joblib"),
    "SVM": joblib.load(r"output_data\SVM\SVM_model.joblib"),
    "LR": joblib.load(r"output_data\LR\LR_model.joblib"),
    "NB": joblib.load(r"output_data\NB\NB_model.joblib")
}


#input parsing
url = input("Enter URL: ").strip().lower()
url = url.replace("http://", "").replace("https://", "")



features = extract_features(url)
features = np.array(features).reshape(1, -1)

# scale 
features = scaler.transform(features)



print("\n Predictions:\n")

for name, model in models.items():
    pred = model.predict(features)[0]

    label = "Phishing " if pred == 0 else "Legitimate "

    print(f"{name}: {label}")