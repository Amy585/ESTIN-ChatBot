import json
import re

class RuleModel:
    def __init__(self, rules_file='rules.json', knowledge_file='data.json'):
        self.rules = self._load_rules(rules_file)
        self.knowledge_base = self._load_knowledge(knowledge_file)

    def _load_rules(self, rules_file):
        """Loads rules dictionary from a specified JSON file."""
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                print(f"Loading rules from {rules_file}...")
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Rules file '{rules_file}' not found. Using an empty rule set.")
            return {} # Return an empty dict to prevent app crash
        except json.JSONDecodeError:
            print(f"Error: Rules file '{rules_file}' is not valid JSON.")
            return {}

    def _load_knowledge(self, knowledge_file):
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Knowledge file '{knowledge_file}' not found.")
            return {}

    def smart_fallback(self, user_input_lower):
        # Your existing smart_fallback logic remains here
        if any(word in user_input_lower for word in ["when", "what time", ...]):
            return "I can help with timing questions! Try asking about:..."
        # ... and so on

    def get_response(self, user_input):
        user_input_lower = user_input.lower()
        
        # 1. Intent Matching (combined for simplicity)
        scores = {}
        for intent, keywords in self.rules.items():
            score = 0
            for keyword in keywords:
                # Use a slightly less strict search if desired, but your \b is good
                if re.search(rf'\b{keyword}\b', user_input_lower):
                    score += 1
            scores[intent] = score
        
        best_intent = max(scores, key=scores.get)
        
        if scores[best_intent] > 0:
            return self.knowledge_base.get(best_intent, "I'm sorry, I don't have an answer for that yet.")
        else:
            # 2. Smart Fallback
            return self.smart_fallback(user_input_lower)