import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, Flatten
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences


#load the data
def load_data(file_path):
    urls=[]
    labels=[]

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue
            label, url = parts
            urls.append(url)
            labels.append(label)
    
    return urls,np.array(labels)



train_urls,y_train=load_data('dataset/train/train.txt')
test_urls,y_test=load_data('dataset/test/test.txt')


#encoder labels


encoder=LabelEncoder()
y_train=encoder.fit_transform(y_train)
y_test=encoder.transform(y_test)


#tokenize urls
tokenizer = Tokenizer()
tokenizer.fit_on_texts(train_urls)

X_train=tokenizer.texts_to_sequences(train_urls)
X_test=tokenizer.texts_to_sequences(test_urls)

#pad the seq
#we are using maxlen as 200 to model the reaserch paper

max_len=200
X_train = pad_sequences(X_train, maxlen=max_len)
X_test = pad_sequences(X_test, maxlen=max_len)

#ann model

model = Sequential()
model.add(Embedding(input_dim=len(tokenizer.word_index)+1, output_dim=32, input_length=max_len))
model.add(Flatten())
model.add(Dense(32, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

y_pred = (model.predict(X_test) > 0.5).astype(int)

print("Accuracy:", accuracy_score(y_test, y_pred))