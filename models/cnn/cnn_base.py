from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv1D, MaxPooling1D,GlobalMaxPooling1D    

from tensorflow.keras.layers import Embedding

class CnnBase:
    def __init__(self, embed_dim: int, sequence_length: int):

        self.embed_dim       = embed_dim
        self.sequence_length = sequence_length
    
    def build(self,char_index:dict)->Sequential:
        voc_size=len(char_index)
        print(f"[CnnBase] voc_size: {voc_size}")
        model=Sequential(name="cnn_base")
        model.add(Embedding(voc_size+1,self.embed_dim,input_length=self.sequence_length,name="embedding"))
        model.add(Conv1D(128,3,activation="tanh",name="conv1"))
        model.add(Flatten(name="flatten"))
        model.add(Dense(1,activation="sigmoid",name="output"))
        return model
    

