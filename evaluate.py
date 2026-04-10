"""
evaluate.py
-----------
Trains (or loads) a model and saves all test_results artifacts:

    test_results/
      {category}/
        {model_name}/
          accuracy.png
          loss.png
          confusion_matrix.png
          normalized_confusion_matrix.png
          classification_report.txt
          model_summary.txt
          model.json
          char_embeddings.json
          raw_test_results.json
          model_all.h5
          weights.h5
          gpu_utilization.png
          floyd_command.txt

Usage examples
--------------
  python evaluate.py --category baseline      --model ann_base    --epochs 10
  python evaluate.py --category big_dataset   --model cnn_complex --epochs 20
  python evaluate.py --category complex_arch  --model att_complex --epochs 15
  python evaluate.py --category complex_cnn   --model cnn_complex2 --epochs 10
  python evaluate.py --category traditional_ml --model cnn_base   --epochs 5
"""

import argparse
import json
import os
import sys
import time
import threading

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)

import tensorflow as tf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from feature_extraction import FeatureExtractor

# ------------------------------------------------------------------ #
# Model registry
# ------------------------------------------------------------------ #

def get_model_builder(model_name: str, embed_dim: int, sequence_length: int):
    
    from models.cnn.cnn_base    import CnnBase
    from models.cnn.cnn_complex import CnnComplex
    from models.rnn.rnn_base    import RnnBase
    from models.rnn.rnn_complex import RnnComplex
    from models.brnn.brnn_base    import BrnnBase
    from models.brnn.brnn_complex import BrnnComplex
    from models.att.att_base    import AttBase
    from models.att.att_complex import AttComplex

    registry = {
        
        "cnn_base":     CnnBase,
        "cnn_complex":  CnnComplex,
        "rnn_base":     RnnBase,
        "rnn_complex":  RnnComplex,
        "brnn_base":    BrnnBase,
        "brnn_complex": BrnnComplex,
        "att_base":     AttBase,
        "att_complex":  AttComplex,
    }

    if model_name not in registry:
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {list(registry.keys())}"
        )
    return registry[model_name](embed_dim, sequence_length)


# ------------------------------------------------------------------ #
# GPU utilization monitor (background thread)
# ------------------------------------------------------------------ #

class GpuMonitor:
    """Polls nvidia-smi every second and records GPU utilisation (%)."""

    def __init__(self):
        self.readings: list = []
        self._stop    = threading.Event()
        self._thread  = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()

    def _poll(self):
        import subprocess
        while not self._stop.is_set():
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=utilization.gpu",
                     "--format=csv,noheader,nounits"],
                    stderr=subprocess.DEVNULL,
                ).decode().strip()
                self.readings.append(float(out.split("\n")[0]))
            except Exception:
                self.readings.append(0.0)
            time.sleep(1)

    def save_plot(self, path: str):
        fig, ax = plt.subplots(figsize=(10, 4))
        if self.readings:
            ax.plot(self.readings, color="green", linewidth=1.2)
            ax.fill_between(range(len(self.readings)), self.readings, alpha=0.25, color="green")
            ax.set_ylim(0, 100)
        else:
            ax.text(0.5, 0.5, "No GPU detected", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, color="grey")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("GPU Utilisation (%)")
        ax.set_title("GPU Utilisation During Training")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)


# ------------------------------------------------------------------ #
# Plotting helpers
# ------------------------------------------------------------------ #

def plot_accuracy(history, path: str):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(history.history["accuracy"],     label="Train Accuracy",      linewidth=1.5)
    ax.plot(history.history["val_accuracy"], label="Validation Accuracy", linewidth=1.5, linestyle="--")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy")
    ax.set_title("Model Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_loss(history, path: str):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(history.history["loss"],     label="Train Loss",      linewidth=1.5)
    ax.plot(history.history["val_loss"], label="Validation Loss", linewidth=1.5, linestyle="--")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Model Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_confusion(cm, labels, path: str, normalize: bool = False):
    title  = "Normalized Confusion Matrix" if normalize else "Confusion Matrix"
    values = cm.astype("float") / cm.sum(axis=1, keepdims=True) if normalize else cm
    fmt    = ".2f" if normalize else "d"

    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=values, display_labels=labels)
    disp.plot(ax=ax, colorbar=True, values_format=fmt)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main(args):
    out_dir = os.path.join("test_results", args.category, args.model)
    os.makedirs(out_dir, exist_ok=True)
    print(f"[evaluate] Output directory: {out_dir}")

    # ---- floyd_command.txt ----------------------------------------
    floyd_cmd = " ".join(sys.argv)
    with open(os.path.join(out_dir, "floyd_command.txt"), "w") as f:
        f.write(floyd_cmd + "\n")

    # ---- Feature extraction --------------------------------------
    fe = FeatureExtractor(char_index_path="dataset/char_index")
    fe.load_from_file("dataset/train/train.txt")
    x_train = fe.get_sequences(sequence_length=args.sequence_length)
    y_train = fe.get_labels()

    fe_test = FeatureExtractor(char_index_path="dataset/char_index")
    fe_test.load_from_file("dataset/test/test.txt")
    x_test = fe_test.get_sequences(sequence_length=args.sequence_length)
    y_test = fe_test.get_labels()

    # ---- char_embeddings.json ------------------------------------
    char_index = fe.tokener.word_index
    with open(os.path.join(out_dir, "char_embeddings.json"), "w") as f:
        json.dump(char_index, f, indent=2)

    # ---- Build model ---------------------------------------------
    builder = get_model_builder(args.model, args.embed_dim, args.sequence_length)
    model   = builder.build(char_index)
    model.compile(
        loss="binary_crossentropy",
        optimizer="adam",
        metrics=["accuracy"],
    )

    # ---- model_summary.txt ---------------------------------------
    with open(os.path.join(out_dir, "model_summary.txt"), "w", encoding="utf-8") as f:
        model.summary(print_fn=lambda line: f.write(line + "\n"))

    # ---- model.json ----------------------------------------------
    with open(os.path.join(out_dir, "model.json"), "w") as f:
        f.write(model.to_json(indent=2))

    # ---- GPU monitor start ---------------------------------------
    gpu_monitor = GpuMonitor()
    gpu_monitor.start()
    t_start = time.time()

    # ---- Train ---------------------------------------------------
    history = model.fit(
        x_train, y_train,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=0.2,
        verbose=1,
    )

    t_end = time.time()
    gpu_monitor.stop()
    training_time = t_end - t_start

    # ---- Save weights / full model --------------------------------
    model.save_weights(os.path.join(out_dir, "weights.weights.h5"))
    model.save(os.path.join(out_dir, "model_all.keras"))

    # ---- Training curve plots ------------------------------------
    plot_accuracy(history, os.path.join(out_dir, "accuracy.png"))
    plot_loss(history,     os.path.join(out_dir, "loss.png"))

    # ---- GPU utilisation plot ------------------------------------
    gpu_monitor.save_plot(os.path.join(out_dir, "gpu_utilization.png"))

    # ---- Evaluate on test set ------------------------------------
    print("[evaluate] Running inference on test set...")
    y_pred_prob = model.predict(x_test, batch_size=args.batch_size, verbose=0).flatten()
    y_pred      = (y_pred_prob >= 0.5).astype(int)

    labels = ["phishing", "legitimate"]

    # ---- Confusion matrices --------------------------------------
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion(cm, labels, os.path.join(out_dir, "confusion_matrix.png"),            normalize=False)
    plot_confusion(cm, labels, os.path.join(out_dir, "normalized_confusion_matrix.png"), normalize=True)

    # ---- Classification report -----------------------------------
    report = classification_report(y_test, y_pred, target_names=labels)
    print(report)
    with open(os.path.join(out_dir, "classification_report.txt"), "w") as f:
        f.write(report)

    # ---- raw_test_results.json -----------------------------------
    raw = {
        "model":          args.model,
        "category":       args.category,
        "epochs":         args.epochs,
        "batch_size":     args.batch_size,
        "embed_dim":      args.embed_dim,
        "sequence_length": args.sequence_length,
        "training_time_seconds": round(training_time, 2),
        "test_accuracy":  float(np.mean(y_pred == y_test)),
        "y_true":         y_test.tolist(),
        "y_pred":         y_pred.tolist(),
        "y_pred_prob":    y_pred_prob.tolist(),
        "history": {
            "accuracy":     history.history["accuracy"],
            "val_accuracy": history.history["val_accuracy"],
            "loss":         history.history["loss"],
            "val_loss":     history.history["val_loss"],
        },
    }
    with open(os.path.join(out_dir, "raw_test_results.json"), "w") as f:
        json.dump(raw, f, indent=2)

    print(f"[evaluate] All results saved to: {out_dir}")
    print(f"[evaluate] Test accuracy: {raw['test_accuracy']:.4f}")
    print(f"[evaluate] Training time: {training_time:.1f}s")


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate a URL phishing model.")
    parser.add_argument("--category",        type=str, default="baseline",
                        choices=["baseline", "big_dataset", "complex_arch", "complex_cnn", "traditional_ml"],
                        help="Result category folder name")
    parser.add_argument("--model",           type=str, default="ann_base",
                        help="Model name (e.g. ann_base, cnn_complex, rnn_base ...)")
    parser.add_argument("--embed_dim",       type=int, default=128)
    parser.add_argument("--sequence_length", type=int, default=512)
    parser.add_argument("--epochs",          type=int, default=10)
    parser.add_argument("--batch_size",      type=int, default=32)
    args = parser.parse_args()

    main(args)