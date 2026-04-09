import json
import re
from tensorflow.keras.preprocessing.text import Tokenizer



def load_data(file_path):
    urls=[]
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue
            url = parts[1]
            url=url.lower().replace("http://","").replace("https://","").replace("www.",""
                                                                                 )
            urls.append(url)
    
    return urls


def main():
    urls=load_data("dataset/train/train.txt")

    tokener=Tokenizer(lower=True,char_level=True,oov_token="-n-")
    tokener.fit_on_texts(urls)

    char_index=tokener.word_index
    with open("dataset/char_index","w") as f:
        f.write(json.dumps(char_index))

if __name__ == '__main__':
    main()