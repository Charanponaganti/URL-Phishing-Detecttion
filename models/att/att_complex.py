from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Dense, LSTM, Bidirectional, Embedding, MultiHeadAttention,
    Flatten, Dropout, Input, LayerNormalization
)


class AttComplex:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Model:
        voc_size = len(char_index)
        print(f"[AttComplex] voc_size: {voc_size}")

        inputs = Input(shape=(self.sequence_length,), name="input")

        x = Embedding(voc_size + 1, self.embed_dim,
                      input_length=self.sequence_length, name="embedding")(inputs)

        # --- Block 1: LSTM → Attention ---
        x = LSTM(128, return_sequences=True, name="lstm1")(x)
        x = Dropout(0.2, name="drop1")(x)

        x = Bidirectional(LSTM(128, return_sequences=True), name="bilstm1")(x)
        x = Dropout(0.2, name="drop2")(x)

        # Self-attention + residual + norm
        attn1 = MultiHeadAttention(num_heads=4, key_dim=self.embed_dim,
                                   name="attention1")(x, x)
        x = LayerNormalization(name="norm1")(x + attn1)
        x = Dropout(0.2, name="drop3")(x)

        # --- Block 2: BiLSTM → LSTM → Attention ---
        x = Bidirectional(LSTM(128, return_sequences=True), name="bilstm2")(x)
        x = Dropout(0.2, name="drop4")(x)

        x = LSTM(128, return_sequences=True, name="lstm2")(x)
        x = Dropout(0.2, name="drop5")(x)

        attn2 = MultiHeadAttention(num_heads=4, key_dim=self.embed_dim,
                                   name="attention2")(x, x)
        x = LayerNormalization(name="norm2")(x + attn2)
        x = Dropout(0.2, name="drop6")(x)

        # --- Block 3: final LSTM ---
        x = LSTM(128, return_sequences=True, name="lstm3")(x)
        x = Dropout(0.2, name="drop7")(x)

        # --- Output ---
        x = Flatten(name="flatten")(x)
        outputs = Dense(1, activation="sigmoid", name="output")(x)

        model = Model(inputs, outputs, name="att_complex")
        return model