import re
import json
import numpy as np
from urllib.parse import urlparse
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing import sequence as keras_sequence
from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing



class FeatureExtractor:
    def __init__(self, char_index_path="../dataset/char_index"):
        # load tokenizer
        self.tokener = Tokenizer(lower=True, char_level=True, oov_token="-n-")
        self.tokener.word_index = json.loads(open(char_index_path).read())
        self.urls = []
        self.labels = []

    def load_from_file(self, filepath):
        # load data from txt file
        self.urls = []
        self.labels = []
        with open(filepath, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        print(f"Loading from {filepath}...")
        skipped = 0
        for line in tqdm(lines, desc="loading"):
            parts = [p for p in line.split("\t") if p]
            if len(parts) < 2:
                skipped += 1
                continue

            label_str, url = parts[0], parts[1]
            if label_str == "phishing":
                label = 1  # positive class in paper
            elif label_str == "legitimate":
                label = 0
            else:
                skipped += 1
                continue

            # normalize url - keep protocol as per paper Fig 4
            clean = url.lower()
            self.urls.append(clean)
            self.labels.append(label)
        print(f"done: {len(self.urls)} urls")

    def get_sequences(self, sequence_length=200):
        # convert urls to numbers
        self._check_loaded()
        seqs = self.tokener.texts_to_sequences(self.urls)
        padded = keras_sequence.pad_sequences(seqs, maxlen=sequence_length)
        return padded

    def get_handcrafted(self, n_jobs=-1):
        # compute manual features in parallel
        self._check_loaded()
        cores = multiprocessing.cpu_count() if n_jobs == -1 else n_jobs
        print(f"extracting on {cores} cores...")
        results = Parallel(n_jobs=cores)(
            delayed(self._extract_one)(u) for u in tqdm(self.urls, desc="features")
        )
        return np.array(results, dtype=np.float32)

    def get_labels(self):
        # return labels array
        self._check_loaded()
        return np.array(self.labels, dtype=np.int32)

    