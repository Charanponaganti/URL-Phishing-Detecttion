from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv1D, MaxPooling1D,GlobalMaxPooling1D    

from tensorflow.keras.layers import Embedding

class CnnComplex:
    def __init__(self, embed_dim: int, sequence_length: int):
        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length

    def build(self, char_index: dict) -> Sequential:
        voc_size=len(char_index)
        print(f"[CnnComplex] voc_size: {voc_size}")
        model=Sequential(name="cnn_complex")
        model.add(Embedding(voc_size+1,self.embed_dim,input_length=self.sequence_length,name="embedding"))

        #block1
        model.add(Conv1D(128,3,activation="tanh",name="conv1")
                  )
        model.add(MaxPooling1D(3,name="pool1"))

        model.add(Conv1D(256, 7, activation="tanh", padding="same", name="conv2"))
        model.add(Conv1D(96,  5, activation="tanh", padding="same", name="conv3"))
        model.add(Conv1D(128, 3, activation="tanh", padding="same", name="conv4"))
        model.add(MaxPooling1D(3, name="pool2"))

        model.add(Conv1D(196, 5, activation="tanh", padding="same", name="conv5"))
        model.add(Conv1D(128, 3, activation="tanh", padding="same", name="conv6"))
        model.add(Conv1D(96,  5, activation="tanh", padding="same", name="conv7"))
        model.add(Conv1D(128, 3, activation="tanh", padding="same", name="conv8"))
        model.add(Conv1D(196, 5, activation="tanh", padding="same", name="conv9"))
        model.add(Conv1D(128, 7, activation="tanh", padding="same", name="conv10"))
        model.add(Conv1D(96,  3, activation="tanh", padding="same", name="conv11"))
        model.add(MaxPooling1D(3, name="pool3"))

        model.add(Conv1D(196, 5, activation="tanh", padding="same", name="conv12"))
        model.add(Conv1D(128, 7, activation="tanh", padding="same", name="conv13"))
        model.add(MaxPooling1D(3, name="pool4"))

        model.add(Conv1D(196, 5, activation="tanh", padding="same", name="conv14"))
        model.add(Conv1D(128, 7, activation="tanh", padding="same", name="conv15"))
        model.add(Conv1D(96,  3, activation="tanh", padding="same", name="conv16"))

        # --- output ---
        model.add(Flatten(name="flatten"))
        model.add(Dense(1, activation="sigmoid", name="output"))

        return model
