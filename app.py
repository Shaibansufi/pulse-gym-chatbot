import json
import os
import base64
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
CORS(app)

# ---------------------------
# Load intents
# ---------------------------
with open("intents.json") as file:
    intents_data = json.load(file)

# ---------------------------
# User session state
# ---------------------------
user_state = {}

# ---------------------------
# Google Credentials (BASE64)
# ---------------------------
def get_google_creds():
    creds_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")

    if not creds_base64:
        raise Exception("Missing GOOGLE_CREDENTIALS_BASE64")

    creds_json = base64.b64decode(creds_base64).decode("utf-8")
    return json.loads(creds_json)

# ---------------------------
# Save Lead to Google Sheets
# ---------------------------
def save_lead(name, email):
    try:
        creds_dict = get_google_creds()

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sheet = client.open_by_key("1a0INWDWyTGb1XXQcx4lYzCvO8tp8blX3bI8LcbR7dTA").sheet1

        sheet.append_row([name, email])

        return "✅ SUCCESS"

    except Exception as e:
        return f"❌ ERROR: {str(e)}"
# ---------------------------
# Intent Matching
# ---------------------------
def get_response(message):
    message = message.lower()

    for intent in intents_data["intents"]:
        for pattern in intent["patterns"]:
            if pattern.lower() in message:
                return random.choice(intent["responses"]), intent["tag"]

    return "I can help with gym info 💪", None

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return "🔥 LeadPulse AI Backend Running"

# 🔥 Test Google Sheets directly
@app.route("/test")
def test():
    try:
        result = save_lead("Test User", "test@gmail.com")
        return f"Result: {result}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"
    try:
        success = save_lead("Test User", "test@gmail.com")
        if success:
            return "✅ SUCCESS: Data written to Google Sheets"
        else:
            return "❌ Failed to write data"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# ---------------------------
# Chat Endpoint
# ---------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower()
    user_id = data.get("user_id", "default_user")

    # Initialize user state
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "name": ""}

    state = user_state[user_id]

    # ---------------------------
    # LEAD FLOW
    # ---------------------------
    if state["step"] == "ask_name":
        state["name"] = message.title()
        state["step"] = "ask_email"
        return jsonify({
            "response": f"Great {state['name']}! Please share your email 📧"
        })

    elif state["step"] == "ask_email":
        email = message
        success = save_lead(state["name"], email)

        state["step"] = None

        if success:
            return jsonify({
                "response": f"Thank you {state['name']}! 🎉 Our team will contact you soon.\nAnything else I can help you with? 💪"
            })
        else:
            return jsonify({
                "response": "Something went wrong saving your details 😅 Please try again."
            })

    # ---------------------------
    # INTENT RESPONSE
    # ---------------------------
    response, tag = get_response(message)

    # 🔥 Trigger lead capture
    if tag == "interest":
        state["step"] = "ask_name"
        return jsonify({
            "response": "Great! 💪 Let's get you started.\nCan I have your name?"
        })

    return jsonify({"response": response})

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)