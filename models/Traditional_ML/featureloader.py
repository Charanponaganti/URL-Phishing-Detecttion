import os
import numpy as np
from feature_extraction import FeatureExtractor

# -------- PATH SETUP -------- #

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_ROOT = os.path.join(SCRIPT_DIR, "dataset")
if not os.path.isdir(DATA_ROOT):
    DATA_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "dataset"))

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "precomputed_features")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------- FUNCTION -------- #

def process_split(split_name):
    print(f"\n Processing {split_name}...")

    file_path = os.path.join(DATA_ROOT, split_name, f"{split_name}.txt")

    fe = FeatureExtractor()
    fe.load_from_file(file_path)

    X = fe.get_handcrafted()
    y = fe.get_labels()

    # Save
    np.save(os.path.join(OUTPUT_DIR, f"X_{split_name}.npy"), X)
    np.save(os.path.join(OUTPUT_DIR, f"y_{split_name}.npy"), y)

    print(f" Saved {split_name} features:")
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")


# -------- MAIN -------- #

if __name__ == "__main__":
    for split in ["train", "val", "test"]:
        process_split(split)

    print("\n All features precomputed and saved!")