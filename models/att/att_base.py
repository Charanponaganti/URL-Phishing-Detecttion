from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Dense, LSTM, Embedding, MultiHeadAttention,
    Flatten, Dropout, Input, GlobalAveragePooling1D
)


class AttBase:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Model:
        voc_size = len(char_index)
        print(f"[AttBase] voc_size: {voc_size}")

        # --- Functional API needed for MultiHeadAttention (query + value args) ---
        inputs = Input(shape=(self.sequence_length,), name="input")

        x = Embedding(voc_size + 1, self.embed_dim,
                      input_length=self.sequence_length, name="embedding")(inputs)

        # Self-attention: query and value are the same tensor
        x = MultiHeadAttention(num_heads=4, key_dim=self.embed_dim,
                               name="self_attention")(x, x)

        x = GlobalAveragePooling1D(name="gap")(x)

        outputs = Dense(1, activation="sigmoid", name="output")(x)

        model = Model(inputs, outputs, name="att_base")
        return model