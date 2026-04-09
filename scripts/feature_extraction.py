import re
import json
import numpy as np
from urllib.parse import urlparse
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing import sequence as keras_sequence

FEATURE_NAMES = [
    # --- length-based ---
    "url_length",           # total character count of the raw URL
    "domain_length",        # length of the domain/hostname only
    "path_length",          # length of the path component
    "subdomain_count",      # number of subdomains (dots in hostname - 1)
    "path_depth",           # number of '/' in the path

    # --- character counts ---
    "count_dots",           # '.'  often high in phishing (e.g. a.b.c.evil.com)
    "count_hyphens",        # '-'  common in spoofed domains
    "count_underscores",    # '_'
    "count_slashes",        # '/'
    "count_at",             # '@'  e.g. http://legit.com@evil.com
    "count_question",       # '?'  query string presence
    "count_equals",         # '='
    "count_ampersand",      # '&'
    "count_percent",        # '%'  URL encoding tricks
    "count_digits",         # total digit characters in URL

    # --- ratio-based ---
    "digit_ratio",          # digits / total length
    "letter_ratio",         # letters / total length
    "special_char_ratio",   # non-alphanumeric / total length

    # --- entropy ---
    "url_entropy",          # Shannon entropy of full URL (randomness indicator)
    "domain_entropy",       # Shannon entropy of domain only

    # --- binary flags ---
    "has_ip_address",       # 1 if hostname looks like an IP (e.g. 192.168.1.1)
    "has_port",             # 1 if URL specifies a port number
    "has_https",            # 1 if scheme is https
    "has_http",             # 1 if scheme is http
    "has_at_symbol",        # 1 if '@' present anywhere
    "has_double_slash",     # 1 if '//' appears in path (redirect trick)
    "has_dash_in_domain",   # 1 if '-' present in domain
    "is_shortened",         # 1 if domain matches known URL shortener list
]

# Common URL shortener domains
_SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co",
    "buff.ly", "rebrand.ly", "cutt.ly", "is.gd", "bl.ink",
    "short.io", "tiny.cc", "lc.chat", "soo.gd", "s2r.co",
}




class FeatureExtractor:

    def __init__(self, char_index_path: str = "../dataset/char_index"):
        """
        Parameters
        ----------
        char_index_path : str
            Path to the saved char_index JSON file produced during training.
        """
        self.tokener = Tokenizer(lower=True, char_level=True, oov_token="-n-")
        self.tokener.word_index = json.loads(open(char_index_path).read())

        self._urls:   list = []
        self._labels: list = []

    # ---------------------------------------------------------------- #
    # Loading
    # ---------------------------------------------------------------- #

    def load_from_file(self, filepath: str) -> None:
        """
        Read a tab-separated dataset file and store URLs + labels.

        Parameters
        ----------
        filepath : str
            Path to train.txt / test.txt / val.txt
        """
        self._urls   = []
        self._labels = []

        with open(filepath, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        skipped = 0
        for line in lines:
            parts = [p for p in line.split("\t") if p]
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

            # strip scheme for consistency (same as dl_gen.py)
            clean_url = url.lower().replace("http://", "").replace("https://", "")
            self._urls.append(clean_url)
            self._labels.append(label)

        print("[FeatureExtractor] Loaded {} URLs ({} skipped) from {}".format(
            len(self._urls), skipped, filepath))

    # ---------------------------------------------------------------- #
    # Feature outputs
    # ---------------------------------------------------------------- #

    def get_sequences(self, sequence_length: int = 512) -> np.ndarray:
        """
        Char-level tokenized + padded sequences.

        Returns
        -------
        np.ndarray of shape (N, sequence_length)
        """
        self._check_loaded()
        seqs = self.tokener.texts_to_sequences(self._urls)
        padded = keras_sequence.pad_sequences(seqs, maxlen=sequence_length)
        print("[FeatureExtractor] Sequences shape: {}".format(padded.shape))
        return padded

    def get_handcrafted(self) -> np.ndarray:
        """
        Handcrafted numerical feature matrix.

        Returns
        -------
        np.ndarray of shape (N, len(FEATURE_NAMES))
        """
        self._check_loaded()
        matrix = np.array([self._extract_one(url) for url in self._urls], dtype=np.float32)
        print("[FeatureExtractor] Handcrafted features shape: {} | features: {}".format(
            matrix.shape, len(FEATURE_NAMES)))
        return matrix

    def get_labels(self) -> np.ndarray:
        """
        Integer labels. 0 = phishing, 1 = legitimate.

        Returns
        -------
        np.ndarray of shape (N,)
        """
        self._check_loaded()
        return np.array(self._labels, dtype=np.int32)

    def get_feature_names(self) -> list:
        """Returns the ordered list of handcrafted feature names."""
        return FEATURE_NAMES.copy()

    # ---------------------------------------------------------------- #
    # Single URL feature extraction
    # ---------------------------------------------------------------- #

    def _extract_one(self, url: str) -> list:
        """Extract all handcrafted features for a single URL string."""

        # re-add scheme so urlparse works correctly
        parse_url = "http://" + url if not url.startswith("http") else url
        parsed    = urlparse(parse_url)
        domain    = parsed.hostname or ""
        path      = parsed.path or ""
        full      = url  # use cleaned (no scheme) for length/char counts

        length        = len(full)
        domain_len    = len(domain)
        path_len      = len(path)

        # --- length-based ---
        subdomain_count = max(domain.count(".") - 1, 0)
        path_depth      = path.count("/")

        # --- character counts ---
        count_dots        = full.count(".")
        count_hyphens     = full.count("-")
        count_underscores = full.count("_")
        count_slashes     = full.count("/")
        count_at          = full.count("@")
        count_question    = full.count("?")
        count_equals      = full.count("=")
        count_ampersand   = full.count("&")
        count_percent     = full.count("%")
        count_digits      = sum(c.isdigit() for c in full)

        # --- ratio-based ---
        digit_ratio       = count_digits / length if length else 0
        letter_ratio      = sum(c.isalpha() for c in full) / length if length else 0
        special_ratio     = sum(not c.isalnum() for c in full) / length if length else 0

        # --- entropy ---
        url_entropy    = self._shannon_entropy(full)
        domain_entropy = self._shannon_entropy(domain)

        # --- binary flags ---
        has_ip          = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain)))
        has_port        = int(parsed.port is not None)
        has_https       = int(parse_url.startswith("https"))
        has_http        = int(parse_url.startswith("http://"))
        has_at          = int("@" in full)
        has_double_sl   = int("//" in path)
        has_dash_domain = int("-" in domain)
        is_shortened    = int(domain in _SHORTENERS)

        return [
            length, domain_len, path_len, subdomain_count, path_depth,
            count_dots, count_hyphens, count_underscores, count_slashes,
            count_at, count_question, count_equals, count_ampersand,
            count_percent, count_digits,
            digit_ratio, letter_ratio, special_ratio,
            url_entropy, domain_entropy,
            has_ip, has_port, has_https, has_http, has_at,
            has_double_sl, has_dash_domain, is_shortened,
        ]

    # ---------------------------------------------------------------- #
    # Helpers
    # ---------------------------------------------------------------- #

    @staticmethod
    def _shannon_entropy(s: str) -> float:
        """Shannon entropy of a string — higher means more random/suspicious."""
        if not s:
            return 0.0
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        n = len(s)
        return -sum((v / n) * np.log2(v / n) for v in freq.values())

    def _check_loaded(self):
        if not self._urls:
            raise RuntimeError("No data loaded. Call load_from_file() first.")

