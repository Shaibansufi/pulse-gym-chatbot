from flask import Flask, request, jsonify
from flask_cors import CORS
import json, random, csv, string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
app = Flask(__name__)
CORS(app)

# Load intents
with open("intents.json") as file:
    data = json.load(file)

patterns, tags = [], []
responses = {}
for intent in data["intents"]:
    for pattern in intent["patterns"]:
        patterns.append(pattern)
        tags.append(intent["tag"])
    responses[intent["tag"]] = intent["responses"]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(patterns)

# Lead capture
leads = {}
current_step = {}  # user context

def normalize(text):
    return text.lower().translate(str.maketrans('', '', string.punctuation))

def get_response(user_input):
    user_vec = vectorizer.transform([user_input])
    similarity = cosine_similarity(user_vec, X)
    index = similarity.argmax()
    tag = tags[index]

    if similarity[0][index] < 0.3:
        return "I’m sorry, I didn’t quite get that. Could you rephrase or ask about our services?"
    return random.choice(responses[tag])

def send_followup(reply, lead_completed=False):
    """
    Adds a friendly follow-up message after any bot response.
    """
    if lead_completed:
        followup = " Thanks for sharing! Is there anything else I can help you with? 💪"
    else:
        followup = " Is there anything else I can help you with? 💪"
    return reply + followup


# Your routes here
@app.route("/")
def home():
    return "Pulse Gym Chatbot Backend Running!"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    user_id = "default"

    if user_id not in current_step:
        current_step[user_id] = "normal"

    msg_norm = normalize(user_message)

    # Check "thank_you" first
    thank_keywords = ["thanks", "thank you", "thank you so much", "thanks a lot"]
    if any(word in msg_norm for word in thank_keywords):
        reply = random.choice(responses.get("thank_you", ["You’re welcome!"]))
        return jsonify({"response": send_followup(reply)})

    # Lead capture flow
    if current_step[user_id] == "ask_name":
        name = user_message.strip().title()
        leads[user_id] = {"name": name}
        current_step[user_id] = "ask_email"
        reply = f"Nice to meet you {name}! Please provide your email."
        return jsonify({"response": reply})

    if current_step[user_id] == "ask_email":
        if "@" in user_message:
            leads[user_id]["email"] = user_message.strip()
            # Save to CSV
            with open("leads.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([leads[user_id]["name"], leads[user_id]["email"]])
            current_step[user_id] = "normal"
            reply = "Thanks! We have saved your contact."
            return jsonify({"response": send_followup(reply, lead_completed=True)})
        else:
            return jsonify({"response": "Please enter a valid email address."})

    # Detect clear interest phrases to trigger lead capture
    interest_phrases = ["interested", "want membership", "i like this gym", "join"]
    if current_step[user_id] == "normal" and any(phrase in msg_norm for phrase in interest_phrases):
        current_step[user_id] = "ask_name"
        return jsonify({"response": "Great! Can I have your name to get started?"})

    # FAQ-first approach
    faq_keywords = {
        "membership": ["membership", "plans", "pricing", "cost", "subscription"],
        "timings": ["timings", "hours", "open", "close"],
        "classes": ["classes", "yoga", "zumba", "crossfit", "personal training"],
        "trainers": ["trainers", "coaches", "expert"],
        "location": ["location", "address", "where"]
    }
    for key, keywords in faq_keywords.items():
        if any(word in msg_norm for word in keywords):
            reply = random.choice(responses.get(key, ["Sorry, I don't have info on that."]))
            return jsonify({"response": send_followup(reply)})

    # Fallback TF-IDF
    reply = get_response(user_message)
    return jsonify({"response": send_followup(reply)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render PORT or default 5000 for local testing
    app.run(host="0.0.0.0", port=port)