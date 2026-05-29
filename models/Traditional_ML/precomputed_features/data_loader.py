from feature_extraction import extract_features


def load_data_features(file_path):
    X, y = [], []

    with open(file_path, "r") as f:
        for line in f:
            label, url = line.strip().split("\t")

            X.append(extract_features(url))
            y.append(0 if label == "phishing" else 1)

    return X, y

"""
def load_data_embeddings(file_path, char_embeddings):
    X, y = [], []

    with open(file_path, "r") as f:
        for line in f:
            label, url = line.strip().split("\t")

            X.append(url_to_embedding(url, char_embeddings))
            y.append(0 if label == "phishing" else 1)

    return X, y """