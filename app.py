import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import gspread
import gspread
from google.oauth2.service_account import Credentials  # 🔥
app = Flask(__name__)
CORS(app)

# Store user state (simple session)
user_state = {}


def save_lead(name, email):
    try:
        print("🚀 Attempting to save:", name, email)

        creds_json = os.environ.get("GOOGLE_CREDENTIALS")

        if not creds_json:
            raise Exception("❌ GOOGLE_CREDENTIALS missing")

        print("✅ ENV loaded")

        creds_json = creds_json.replace('\n', '\\n')
        creds_dict = json.loads(creds_json)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        print("✅ Credentials parsed")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        print("✅ Authorized client")

        spreadsheet = client.open_by_key("1a0INWDWyTGb1XXQcx4lYzCvO8tp8blX3bI8LcbR7dTA")
        print("✅ Opened spreadsheet:", spreadsheet.title)

        sheet = spreadsheet.sheet1
        print("✅ Using sheet:", sheet.title)

        # 🔥 FORCE CHECK BEFORE WRITE
        existing = sheet.get_all_values()
        print("📄 Existing rows:", len(existing))

        sheet.append_row([name, email])

        print("🎉 SUCCESS: Row appended")

    except Exception as e:
        print("❌ FULL ERROR:", repr(e))  # 👈 VERY IMPORTANT

@app.route("/")
def home():
    return "Pulse Gym AI Backend Running 💪"


@app.route("/test")
def test():
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")

        if not creds_json:
            return "❌ ENV NOT FOUND"

        creds_json = creds_json.replace('\n', '\\n')
        creds_dict = json.loads(creds_json)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        import gspread
        from google.oauth2.service_account import Credentials

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key("1a0INWDWyTGb1XXQcx4lYzCvO8tp8blX3bI8LcbR7dTA")

        sheet = spreadsheet.sheet1

        sheet.append_row(["TestUser", "test@gmail.com"])

        return "✅ SUCCESS: Data written"

    except Exception as e:
        return f"❌ ERROR: {str(e)}"


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