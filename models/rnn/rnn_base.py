from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Embedding


class RnnBase:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Sequential:
        voc_size = len(char_index)
        print(f"[RnnBase] voc_size: {voc_size}")

        model = Sequential(name="rnn_base")
        model.add(Embedding(voc_size + 1, self.embed_dim,
                            input_length=self.sequence_length, name="embedding"))

        model.add(LSTM(128, name="lstm"))

        model.add(Dense(1, activation="sigmoid", name="output"))

        return model