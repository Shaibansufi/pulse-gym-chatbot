import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import csv

app = Flask(__name__)
CORS(app)

# Store user state (simple session)
user_state = {}

# Save leads to CSV
def save_lead(name, email):
    file_exists = os.path.isfile("leads.csv")
    with open("leads.csv", "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Email"])
        writer.writerow([name, email])

@app.route("/")
def home():
    return "Pulse Gym AI Backend Running 💪"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower()
    user_id = "default_user"  # simple session (can improve later)

    # Initialize user state
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "name": ""}

    state = user_state[user_id]

    # 🔥 LEAD FLOW
    if state["step"] == "ask_name":
        state["name"] = message.title()
        state["step"] = "ask_email"
        return jsonify({"response": f"Great {state['name']}! Please share your email 📧"})

    elif state["step"] == "ask_email":
        email = message
        save_lead(state["name"], email)
        state["step"] = None
        return jsonify({
            "response": f"Thank you {state['name']}! 🎉 Our team will contact you soon.\nIs there anything else I can help you with? 💪"
        })

    # 🔥 SMART KEYWORD MATCHING

    # Timings
    if any(word in message for word in ["time", "timing", "open", "close", "hour", "schedule"]):
        return jsonify({
            "response": "Our gym is open from 6 AM to 10 PM, Monday to Saturday 💪⏰\nAnything else I can help you with?"
        })

    # Membership
    elif any(word in message for word in ["membership", "price", "cost", "fees", "plan", "charge"]):
        return jsonify({
            "response": "We offer flexible plans starting from ₹999/month 💳🔥\nWould you like to join or know more?"
        })

    # Trainers
    elif any(word in message for word in ["trainer", "coach", "personal training"]):
        return jsonify({
            "response": "Yes! We have certified personal trainers available 🏋️‍♂️\nWould you like to join?"
        })

    # Location
    elif any(word in message for word in ["location", "where", "address"]):
        return jsonify({
            "response": "We are located in the city center 📍 Easy to reach!\nWould you like directions?"
        })

    # Interest trigger
    elif any(word in message for word in ["join", "interested", "register", "signup"]):
        state["step"] = "ask_name"
        return jsonify({
            "response": "Awesome! 💪 Let's get you started.\nCan I have your name?"
        })

    # Compliment handling
    elif any(word in message for word in ["good", "nice", "great", "awesome"]):
        return jsonify({
            "response": "Thank you! 😊 Would you like to know about membership or join?"
        })

    # 🔥 FALLBACK (SMART)
    else:
        return jsonify({
            "response": "I can help you with timings ⏰, membership 💳, trainers 🏋️‍♂️, or joining.\nWhat would you like to know? 💪"
        })

# Run for Render + Local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)