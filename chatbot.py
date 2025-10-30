# # chatbot.py
# import json
# import re

# # Load the knowledge base
# with open('data.json', 'r', encoding='utf-8') as f:
#     knowledge_base = json.load(f)

# # Define rules matching your scope
# rules = {
#     "library_opening": ["library", "opens", "opening", "time", "what time", "opens at"],
#     "library_closing": ["library", "closes", "closing", "close", "what time", "closes at"],
#     "courses_start": ["courses", "start", "begin", "what time", "starting", "first session"],
#     "last_session": ["last", "session", "ends", "ending", "what time", "final", "last class"],
#     "administration_hours": ["administration", "available", "when", "open", "hours", "works"],
#     "second_year_program": ["program", "2cs", "second year", "1st", "first semester", "schedule", "timetable"],
#     "specialties_number": ["specialties", "specialities", "how many", "estin has", "branches", "majors"]
# }

# def get_response(user_input):
#     user_input = user_input.lower()
    
#     # Count matches for each intent
#     scores = {}
#     for intent, keywords in rules.items():
#         score = 0
#         for keyword in keywords:
#             if re.search(rf'\b{keyword}\b', user_input):
#                 score += 1
#         scores[intent] = score
    
#     # Get the intent with the highest score
#     best_intent = max(scores, key=scores.get)
    
#     # Only return a response if we have a reasonable match
#     if scores[best_intent] > 0:
#         return knowledge_base.get(best_intent, "I'm sorry, I don't have an answer for that yet.")
#     else:
#         return "I'm not sure I understand. Can you try asking about library hours, course schedules, administration availability, or ESTIN specialties?"

# # Main chat loop
# print("ESTIN Bot: Hello! I'm the ESTIN assistant. How can I help you? (Type 'quit' to exit)")
# while True:
#     user_input = input("You: ")
#     if user_input.lower() == 'quit':
#         print("ESTIN Bot: Goodbye!")
#         break
#     response = get_response(user_input)
#     print(f"ESTIN Bot: {response}")