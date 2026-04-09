from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, Bidirectional, Embedding


class RnnComplex:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Sequential:
        voc_size = len(char_index)
        print(f"[RnnComplex] voc_size: {voc_size}")

        model = Sequential(name="rnn_complex")
        model.add(Embedding(voc_size + 1, self.embed_dim,
                            input_length=self.sequence_length, name="embedding"))

        # --- Block 1: forward LSTM stack ---
        model.add(LSTM(128, return_sequences=True, name="lstm1"))
        model.add(Dropout(0.2, name="drop1"))

        # --- Block 2: bidirectional stack ---
        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm1"))
        model.add(Dropout(0.2, name="drop2"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm2"))
        model.add(Dropout(0.2, name="drop3"))

        model.add(Bidirectional(LSTM(64, return_sequences=True), name="bilstm3"))
        model.add(Dropout(0.2, name="drop4"))

        # --- Block 3: deeper bidirectional ---
        model.add(Bidirectional(LSTM(128, return_sequences=True), name="bilstm4"))
        model.add(Dropout(0.2, name="drop5"))

        model.add(Bidirectional(LSTM(128, return_sequences=True), name="bilstm5"))
        model.add(Dropout(0.2, name="drop6"))

        # --- Block 4: final LSTM (no return_sequences → collapses time axis) ---
        model.add(LSTM(128, name="lstm_final"))
        model.add(Dropout(0.2, name="drop_final"))

        # --- Output ---
        model.add(Dense(1, activation="sigmoid", name="output"))

        return model