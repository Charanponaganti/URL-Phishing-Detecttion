import os
import json

import pandas as pd
import numpy as np

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

import re

#implement the ANN model


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



#feature extraction

def extract_features(url):
    features=[]
    features.append(len(url))                    
    features.append(url.count('.'))            
    features.append(url.count('/'))       
    features.append(url.count('-'))          
    features.append(url.count('@'))         
    features.append(1 if "https" in url else 0)   
    features.append(sum(c.isdigit() for c in url)) 

    suspicious_words = ["login", "verify", "bank", "secure", "account"]
    features.append(sum(word in url for word in suspicious_words))

    return features


train_urls,y_train=load_data('dataset/train/train.txt')
test_urls,y_test=load_data('dataset/test/test.txt')

X_train = np.array([extract_features(url) for url in train_urls])
X_test = np.array([extract_features(url) for url in test_urls])


encoder=LabelEncoder()
y_train=encoder.fit_transform(y_train)
y_test=encoder.transform(y_test)

scaler=StandardScaler()
X_train=scaler.fit_transform(X_train)
X_test=scaler.transform(X_test)

model=Sequential()
model.add(Dense(32,activation='relu',input_shape=(X_train.shape[1],)))
model.add(Dense(32,activation='relu'))
model.add(Dense(1,activation='sigmoid'))

model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])

model.fit(X_train,y_train,epochs=10,batch_size=32,validation_data=(X_test,y_test))


y_pred = (model.predict(X_test) > 0.5).astype(int)

print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))



            