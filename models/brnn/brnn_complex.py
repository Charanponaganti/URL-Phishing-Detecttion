from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, Bidirectional, Embedding


class BrnnComplex:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Sequential:
        voc_size = len(char_index)
        print(f"[BrnnComplex] voc_size: {voc_size}")

        model = Sequential(name="brnn_complex")
        model.add(Embedding(voc_size + 1, self.embed_dim,
                            input_length=self.sequence_length, name="embedding"))

        # --- Block 1 ---
        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm1"))
        model.add(Dropout(0.2, name="drop1"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm2"))
        model.add(Dropout(0.2, name="drop2"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm3"))
        model.add(Dropout(0.2, name="drop3"))

        # --- Block 2 ---
        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm4"))
        model.add(Dropout(0.2, name="drop4"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm5"))
        model.add(Dropout(0.2, name="drop5"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm6"))
        model.add(Dropout(0.2, name="drop6"))

        # --- Final layer (collapses time axis) ---
        model.add(Bidirectional(LSTM(128), name="bilstm_final"))
        model.add(Dropout(0.2, name="drop_final"))

        # --- Output ---
        model.add(Dense(1, activation="sigmoid", name="output"))

        return model