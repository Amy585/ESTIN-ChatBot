import json
import numpy as np
from nltk_utils import tokenize, stem, bag_of_words

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from fnn_model import NeuralNet


with open('faq_data.json', 'r') as f:
    intents = json.load(f)


# Creating lists for all words(vocabulary), tags, and sentence-intent pairs
all_words = []
tags = []
xy = []

for e in intents['intents']:
  tag = e['tag']
  tags.append(tag)
  for pattern in e['patterns']:
    w = tokenize(pattern)
    all_words.extend(w)
    xy.append((w, tag))


ignore = ['?', '!', ',', '.']
all_words = [stem(w) for w in all_words if w not in ignore]

all_words = sorted(set(all_words))
tags = sorted(set(tags))

# Creating training data
X_train = []
y_train = []
for (w, tag) in xy:
  bow = bag_of_words(w, all_words)
  X_train.append(bow)
  label = tags.index(tag)
  y_train.append(label)


X_train = np.array(X_train)
y_train = np.array(y_train)


#Creating the pytorch Dataset
class ChatDataSet (Dataset) :
  def __init__(self):
    self.n_samples = len(X_train)
    self.x_data = X_train
    self.y_data = y_train

  def __getitem__(self, index):
    return self.x_data[index], self.y_data[index]

  def __len__(self) :
    return self.n_samples


#Hyperparameters
batch_size = 8
input_size = len(X_train[0])
hidden_size = 32
num_classes = len(tags)
learning_rate = 0.001
num_epochs = 50


dataset = ChatDataSet()
train_loader = DataLoader(dataset = dataset, batch_size = batch_size, shuffle = True)


#Initializing the model, loss function and optimizer
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, num_classes).to(device)

critereon = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr = learning_rate)


#Training loop
for epoch in range(num_epochs):
  for (words, labels) in train_loader:
    words = words.to(device)
    labels = labels.to(device)

    #forward
    outputs = model(words)

    loss = critereon(outputs, labels)

    #backward and optimizer step
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

  if (epoch + 1) % 10 == 0 :
    print(f'epoch {epoch + 1}/{num_epochs}, loss={loss.item():.4f}')

print(f'final loss: loss={loss.item():.4f}')


#Saving the trained model
data = {
    "model_state" : model.state_dict(),
    "input_size" : input_size,
    "output_size" : num_classes,
    "hidden_size" : hidden_size,
    "all_words" : all_words,
    "tags" : tags
}

FILE = "data.pth"
torch.save(data, FILE)
print(f'training complete. File saved to {FILE}')