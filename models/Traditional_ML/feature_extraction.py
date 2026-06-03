import re
import numpy as np
from urllib.parse import urlparse

FEATURE_NAMES = [
    #structural
    "url_length",
    "domain_length",
    "path_length",
    "subdomain_count",
    "path_depth",

#numerical
    "count_dots",
    "count_hyphens",
    "count_underscores",
    "count_slashes",
    "count_at",
    "count_question",
    "count_equals",
    "count_ampersand",
    "count_percent",
    "count_digits",

#stats
    "digit_ratio",
    "letter_ratio",
    "special_char_ratio",

#entropy
    "url_entropy",
    "domain_entropy",
#binary
    "has_ip_address",
    "has_port",
    "has_https",
    "has_http",
    "has_at_symbol",
    "has_double_slash",
    "has_dash_in_domain",
    "is_shortened",
]

_SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co",
    "buff.ly", "rebrand.ly", "cutt.ly", "is.gd", "bl.ink",
    "short.io", "tiny.cc", "lc.chat", "soo.gd", "s2r.co",
}


class FeatureExtractor:

    def __init__(self):
        self._urls = []
        self._labels = []

    # ---------------- LOAD DATA ---------------- #

#stores clean urls with their respective labels
    def load_from_file(self, filepath: str):
        self._urls = []
        self._labels = []

        with open(filepath, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        skipped = 0

        for line in lines:
            parts = line.split("\t")
            if len(parts) < 2:
                skipped += 1
                continue

            label_str, url = parts[0], parts[1]

            if label_str == "phishing":
                label = 0
            elif label_str == "legitimate":
                label = 1
            else:
                skipped += 1
                continue

            clean_url = url.lower().replace("http://", "").replace("https://", "")
            self._urls.append(clean_url)
            self._labels.append(label)

        print(f"[FeatureExtractor] Loaded {len(self._urls)} samples ({skipped} skipped)")

    # ---------------- OUTPUT ---------------- #

#returns the X matrix
    def get_handcrafted(self):
        self._check_loaded()
        X = np.array([self._extract_one(url) for url in self._urls], dtype=np.float32)
        print(f"[FeatureExtractor] Feature shape: {X.shape}")
        return X

#Returns the Y matrix/vector
    def get_labels(self):
        self._check_loaded()
        return np.array(self._labels, dtype=np.int32)

    def get_feature_names(self):
        return FEATURE_NAMES

    # feature vector for a given url 

    def _extract_one(self, url: str):
        #parsing
        parse_url = "http://" + url
        
        parsed = urlparse(parse_url)
 
 #feature calculation
        domain = parsed.hostname or ""
        path = parsed.path or ""
        full = url

        length = len(full)
        domain_len = len(domain)
        path_len = len(path)

        subdomain_count = max(domain.count(".") - 1, 0)
        path_depth = path.count("/")

        count_dots = full.count(".")
        count_hyphens = full.count("-")
        count_underscores = full.count("_")
        count_slashes = full.count("/")
        count_at = full.count("@")
        count_question = full.count("?")
        count_equals = full.count("=")
        count_ampersand = full.count("&")
        count_percent = full.count("%")
        count_digits = sum(c.isdigit() for c in full)

        digit_ratio = count_digits / length if length else 0
        letter_ratio = sum(c.isalpha() for c in full) / length if length else 0
        special_ratio = sum(not c.isalnum() for c in full) / length if length else 0

        url_entropy = self._entropy(full)
        domain_entropy = self._entropy(domain)

        has_ip = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain)))
        has_port = int(parsed.port is not None)
        has_https = int("https" in parse_url)
        has_http = int("http://" in parse_url)
        has_at = int("@" in full)
        has_double_slash = int("//" in path)
        has_dash_domain = int("-" in domain)
        is_shortened = int(domain in _SHORTENERS)

        return [
            length, domain_len, path_len, subdomain_count, path_depth,
            count_dots, count_hyphens, count_underscores, count_slashes,
            count_at, count_question, count_equals, count_ampersand,
            count_percent, count_digits,
            digit_ratio, letter_ratio, special_ratio,
            url_entropy, domain_entropy,
            has_ip, has_port, has_https, has_http, has_at,
            has_double_slash, has_dash_domain, is_shortened,
        ]

    # ---------------- HELPERS ---------------- #

    def _entropy(self, s: str):
        if not s:
            return 0
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        n = len(s)
        return -sum((v / n) * np.log2(v / n) for v in freq.values())

    def _check_loaded(self):
        if not self._urls:
            raise RuntimeError("No data loaded. Call load_from_file() first.")