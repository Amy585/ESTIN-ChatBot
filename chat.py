import random
from fnn_model import NeuralNet # Assuming this is your model definition
import torch
import json
import numpy as np
from nltk_utils import bag_of_words, tokenize

class FNNModel:
    def __init__(self, intents_file='faq_data.json', model_file="data.pth"):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 1. Load Intents (Knowledge Base)
        try:
            with open(intents_file, 'r', encoding='utf-8') as f:
                self.intents = json.load(f)
        except FileNotFoundError:
            print(f"Error: Intents file '{intents_file}' not found.")
            self.intents = {'intents': []}

        # 2. Load Model Data
        try:
            data = torch.load(model_file)
            self.all_words = data['all_words']
            self.tags = data['tags']
            input_size = data["input_size"]
            hidden_size = data["hidden_size"]
            output_size = data["output_size"]
            model_state = data["model_state"]
            
            # 3. Initialize and Load Model
            self.model = NeuralNet(input_size, hidden_size, output_size).to(self.device)
            self.model.load_state_dict(model_state)
            self.model.eval()
            print("PyTorch Model loaded successfully.")

        except FileNotFoundError:
            print(f"Error: Model file '{model_file}' not found.")
            self.model = None # Set model to None if loading fails

    def get_response(self, msg):
        if not self.model:
            return {"text": "Bot is unavailable. Model file could not be loaded."}
            
        sentence = tokenize(msg)
        X = bag_of_words(sentence, self.all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(self.device)

        output = self.model(X)
        _, predicted = torch.max(output, dim=1)
        tag = self.tags[predicted.item()]

        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        
        # 4. Check Confidence and Find Response
        if prob.item() > 0.75:
            for intent in self.intents['intents']:
                if tag == intent["tag"]:
                    # Return a structured dictionary for the Flask route
                    # Assuming 'response' holds the text, and 'file' holds optional metadata
                    
                    # If response is a list, choose one randomly
                    response_text = random.choice(intent.get('response')) if isinstance(intent.get('response'), list) else intent.get('response')

                    return {
                        "text": response_text,
                        "file": intent.get('file', None) # Include file metadata if available
                    }

        # Fallback response (low confidence)
        return {"text": "I do not understand... Can you please rephrase?"}

