import os
import time
import requests
import smtplib
import threading
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# =========================
# CONFIG
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MODEL_URL = os.getenv("MODEL_URL")

ALERT_EMAIL = os.getenv("ALERT_EMAIL")
ALERT_APP_PASSWORD = os.getenv("ALERT_APP_PASSWORD")
ALERT_RECEIVER = os.getenv("ALERT_RECEIVER")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUCKET_NAME = "captured-images"

# =========================
# 🚨 DANGEROUS ANIMALS
# =========================
DANGEROUS_ANIMALS = [
    "bear","bison","boar","coyote","eagle",
    "elephant","gorilla","hippopotamus","hyena",
    "leopard","lion","rhinoceros","shark",
    "snake","tiger","wolf"
]

# =========================
# 📧 EMAIL FUNCTION (CLOUD SAFE)
# =========================
def send_email_alert(animal, confidence):
    try:
        print("🚨 EMAIL ALERT STARTED")

        subject = f"🚨 DANGER ALERT: {animal.upper()} DETECTED"
        body = f"""
Dangerous animal detected!

Animal: {animal}
Confidence: {confidence:.2f}%

Take precautions immediately.
"""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = ALERT_EMAIL
        msg["To"] = ALERT_RECEIVER

        # ✅ USE TLS 587 (BETTER FOR RENDER)
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()

        print("🔐 Logging into Gmail...")
        server.login(ALERT_EMAIL, ALERT_APP_PASSWORD)

        print("📤 Sending email...")
        server.sendmail(ALERT_EMAIL, ALERT_RECEIVER, msg.as_string())

        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ EMAIL FAILED:", str(e))


# =========================
# PREDICT ENDPOINT
# =========================
@app.route("/predict", methods=["POST"])
def predict():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image_bytes = file.read()

    try:
        print("📷 Sending image to model...")

        files = {"image": (file.filename, image_bytes, file.mimetype)}

        response = requests.post(
            MODEL_URL,
            files=files,
            timeout=120
        )

        response.raise_for_status()
        prediction = response.json()

        animal = prediction.get("label", "Unknown").lower()
        confidence = float(prediction.get("confidence", 0)) * 100

        print("🧠 Prediction:", animal, confidence)

        # 🚀 SEND EMAIL IN BACKGROUND
        if animal in DANGEROUS_ANIMALS:
            print("⚠️ Dangerous animal detected")
            threading.Thread(
                target=send_email_alert,
                args=(animal, confidence),
                daemon=True
            ).start()

        return jsonify({
            "status": "success",
            "animal": animal,
            "confidence": confidence
        }), 200

    except Exception as e:
        print("❌ Prediction failed:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# HEALTH CHECK
# =========================
@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


# =========================
# ROOT
# =========================
@app.route("/")
def root():
    return jsonify({"status": "Backend Running"}), 200


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
