import os
import time
import threading
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ✅ CORS for Vercel frontend
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# =========================
# CONFIG
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MODEL_URL = os.getenv("MODEL_URL")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise Exception("Supabase env variables missing")

if not MODEL_URL:
    raise Exception("MODEL_URL missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =========================
# BACKGROUND STORAGE TASK
# =========================
def background_storage(image_bytes, filename, mimetype, animal, confidence, user_id):
    try:
        bucket = "labeled-images"  # ⚠️ must exist in Supabase

        # Upload image
        supabase.storage.from_(bucket).upload(
            filename,
            image_bytes,
            {"content-type": mimetype}
        )

        # Get public URL
        public_url = supabase.storage.from_(bucket).get_public_url(filename)

        # Insert record
        supabase.table("labeled_images").insert({
            "labeled_image_url": public_url,
            "animal_detected": animal,
            "confidence_score": confidence,
            "user_id": user_id
        }).execute()

        print("✅ Stored detection:", animal)

    except Exception as e:
        print("❌ Background storage error:", e)


# =========================
# PREDICT ENDPOINT
# =========================
@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image_bytes = file.read()
    mimetype = file.mimetype
    user_id = request.form.get("user_id")

    # 🧠 SAFE FALLBACK if user_id missing
    if not user_id:
        user_id = "anonymous"

    try:
        # Send image to HF Space
        files = {"image": (file.filename, image_bytes, mimetype)}

        response = requests.post(
            MODEL_URL,
            files=files,
            timeout=120
        )

        response.raise_for_status()
        prediction = response.json()

        animal = prediction.get("label", "Unknown")
        confidence = float(prediction.get("confidence", 0)) * 100

        # 🔥 FINAL FIX — STORE INSIDE USER FOLDER
        filename = f"{user_id}/{int(time.time())}_{file.filename}"

        threading.Thread(
            target=background_storage,
            args=(image_bytes, filename, mimetype, animal, confidence, user_id),
            daemon=True
        ).start()

        return jsonify({
            "status": "success",
            "animal": animal,
            "confidence": confidence
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


# =========================
# ROOT ROUTE
# =========================
@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "Animal Detection Backend Running"}), 200


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
