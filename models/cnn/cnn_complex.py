from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Dense, Dropout,
    Conv1D, MaxPooling1D, GlobalMaxPooling1D,
    BatchNormalization, Embedding
)


class CnnComplex:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Sequential:
        voc_size = len(char_index)
        print(f"[CnnComplex] voc_size: {voc_size}")

        model = Sequential(name="cnn_complex")

        # ── Embedding ─────────────────────────────────────────────────────────
        # Keep embed_dim small (16–32) on CPU — e.g. CnnComplex(embed_dim=16, ...)
        model.add(Embedding(
            voc_size + 1, self.embed_dim,
            input_length=self.sequence_length,
            name="embedding"
        ))

        # ── Block 1 — local features (kernel 3) ───────────────────────────────
        model.add(Conv1D(64, 3, activation="relu", padding="same", name="conv1"))
        model.add(BatchNormalization(name="bn1"))
        model.add(MaxPooling1D(2, name="pool1"))   # halves sequence length
        model.add(Dropout(0.2, name="drop1"))

        # ── Block 2 — mid-range features (kernel 5) ───────────────────────────
        model.add(Conv1D(128, 5, activation="relu", padding="same", name="conv2"))
        model.add(BatchNormalization(name="bn2"))
        model.add(MaxPooling1D(2, name="pool2"))   # halves again
        model.add(Dropout(0.2, name="drop2"))

        # ── Block 3 — higher-level features (kernel 3) ────────────────────────
        model.add(Conv1D(256, 3, activation="relu", padding="same", name="conv3"))
        model.add(BatchNormalization(name="bn3"))
        model.add(Dropout(0.3, name="drop3"))

        # ── Global pooling — collapses sequence dim entirely ──────────────────
        model.add(GlobalMaxPooling1D(name="global_pool"))

        # ── Classifier head ───────────────────────────────────────────────────
        model.add(Dense(128, activation="relu", name="dense1"))
        model.add(Dropout(0.3, name="drop4"))
        model.add(Dense(1, activation="sigmoid", name="output"))

        return model