# main script for training and testing
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
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import tensorflow as tf
from feature_extraction import FeatureExtractor

# registry for models
def get_model(name, dim, seq):
    from models.cnn.cnn_base import CnnBase
    from models.cnn.cnn_complex import CnnComplex
    from models.rnn.rnn_base import RnnBase
    from models.rnn.rnn_complex import RnnComplex
    from models.brnn.brnn_base import BrnnBase
    from models.brnn.brnn_complex import BrnnComplex
    from models.att.att_base import AttBase
    from models.att.att_complex import AttComplex
    from models.ann.ann_base import AnnBase
    from models.ann.ann_complex import AnnComplex

    mods = {
        "cnn_base": CnnBase, "cnn_complex": CnnComplex,
        "rnn_base": RnnBase, "rnn_complex": RnnComplex,
        "brnn_base": BrnnBase, "brnn_complex": BrnnComplex,
        "att_base": AttBase, "att_complex": AttComplex,
        "ann_base": AnnBase, "ann_complex": AnnComplex
    }
    
    return mods[name](dim, seq)

# monitoring gpu
class GpuMonitor:
    def __init__(self):
        self.readings = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self): self._thread.start()
    def stop(self):
        self._stop.set()
        self._thread.join()

    def _poll(self):
        import subprocess
        while not self._stop.is_set():
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                self.readings.append(float(out.split("\n")[0]))
            except: self.readings.append(0.0)
            time.sleep(1)

    def save_plot(self, path):
        fig, ax = plt.subplots(figsize=(10, 4))
        if self.readings:
            ax.plot(self.readings, color="green")
            ax.fill_between(range(len(self.readings)), self.readings, alpha=0.2, color="green")
        ax.set_ylim(0, 100)
        ax.set_title("gpu usage")
        fig.savefig(path)
        plt.close(fig)

# plots
def plot_acc(hist, path):
    plt.figure()
    plt.plot(hist.history["accuracy"], label="train")
    plt.plot(hist.history["val_accuracy"], label="val")
    plt.legend(); plt.savefig(path); plt.close()

def plot_loss(hist, path):
    plt.figure()
    plt.plot(hist.history["loss"], label="train")
    plt.plot(hist.history["val_loss"], label="val")
    plt.legend(); plt.savefig(path); plt.close()

def run_eval(args):
    dest = os.path.join("test_results", args.category, args.model)
    os.makedirs(dest, exist_ok=True)
    
    # save settings
    with open(os.path.join(dest, "floyd_command.txt"), "w") as f:
        f.write(" ".join(sys.argv))

    extractor = FeatureExtractor(char_index_path="dataset/char_index")
    
    # train data
    extractor.load_from_file("dataset/train/train.txt")
    x_train = extractor.get_sequences(sequence_length=args.sequence_length)
    y_train = extractor.get_labels()

    # test data
    test_ext = FeatureExtractor(char_index_path="dataset/char_index")
    test_ext.load_from_file("dataset/test/test.txt")
    x_test = test_ext.get_sequences(sequence_length=args.sequence_length)
    y_test = test_ext.get_labels()

    # setup model
    builder = get_model(args.model, args.embed_dim, args.sequence_length)
    model = builder.build(extractor.tokener.word_index)
    
    opt = tf.keras.optimizers.Adam(learning_rate=0.01)
    model.compile(loss="binary_crossentropy", optimizer=opt, metrics=["accuracy"])
    
    # training start
    mon = GpuMonitor()
    mon.start()
    start_t = time.time()

    stops = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=2)
    ]

    print("\ntraining model...")
    hist = model.fit(x_train, y_train, epochs=args.epochs, batch_size=args.batch_size, 
                     validation_split=0.2, callbacks=stops)

    end_t = time.time()
    mon.stop()
    duration = end_t - start_t

    # save results
    model.save(os.path.join(dest, "model_all.keras"))
    plot_acc(hist, os.path.join(dest, "accuracy.png"))
    plot_loss(hist, os.path.join(dest, "loss.png"))
    mon.save_plot(os.path.join(dest, "gpu_utilization.png"))

    # infer test
    print("testing...")
    probs = model.predict(x_test, batch_size=args.batch_size, verbose=0).flatten()
    preds = (probs >= 0.5).astype(int)

    # report
    rep = classification_report(y_test, preds, target_names=["legit", "phishing"])
    print(rep)
    with open(os.path.join(dest, "classification_report.txt"), "w") as f: f.write(rep)

    final = {
        "model": args.model, "time": round(duration, 2),
        "accuracy": float(np.mean(preds == y_test)),
        "history": hist.history
    }
    with open(os.path.join(dest, "raw_test_results.json"), "w") as f: json.dump(final, f)
    print(f"done! acc: {final['accuracy']:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, default="baseline")
    parser.add_argument("--model", type=str, default="cnn_base")
    parser.add_argument("--embed_dim", type=int, default=50)
    parser.add_argument("--sequence_length", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=1024)
    run_eval(parser.parse_args())