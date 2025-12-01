import nltk
nltk.download('punkt_tab')
import numpy as np
from nltk.stem.porter import PorterStemmer


#Tokenization process
def tokenize(string):
  return nltk.word_tokenize(string)


#Stemming process
stemmer = PorterStemmer()
def stem(word):
  return stemmer.stem(word.lower())


#Bag of Words 
def bag_of_words(tokenized_sentence, all_words):
  tokenized_sentence = [stem(w) for w in tokenized_sentence]

  bag = np.zeros(len(all_words), dtype = np.float32)
  for idx, w in enumerate(all_words):
    if w in tokenized_sentence:
      bag[idx] = 1.0
  return bag