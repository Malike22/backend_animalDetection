import os
import time
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

BUCKET_NAME = "captured-images"  # MUST EXIST in Supabase


# =========================
# PREDICT ENDPOINT (AI ONLY)
# =========================
@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():

    # 🔥 Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image_bytes = file.read()
    mimetype = file.mimetype

    try:
        # Send image to HF Space model
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

        return jsonify({
            "status": "success",
            "animal": animal,
            "confidence": confidence
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# SAVE HISTORY (UPLOAD + DB INSERT)
# =========================
@app.route("/save-history", methods=["POST"])
def save_history():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    animal = request.form.get("animal")
    confidence = request.form.get("confidence")
    user_id = request.form.get("user_id")

    if not all([animal, confidence, user_id]):
        return jsonify({"error": "Missing required data"}), 400

    try:
        image_bytes = file.read()
        mimetype = file.mimetype
        filename = f"{int(time.time())}_{file.filename}"

        # ========= 1️⃣ Upload to Storage =========
        supabase.storage.from_(BUCKET_NAME).upload(
            filename,
            image_bytes,
            {"content-type": mimetype}
        )

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)

        # ========= 2️⃣ Insert into captured_images =========
        captured_data = {
            "user_id": user_id,
            "image_url": public_url,
            "status": "completed"
        }

        captured_response = supabase.table("captured_images").insert(captured_data).execute()

        if not captured_response.data:
            return jsonify({"error": "Failed to create captured image record"}), 500

        captured_id = captured_response.data[0]["id"]

        # ========= 3️⃣ Insert into labeled_images =========
        label_data = {
            "captured_image_id": captured_id,
            "labeled_image_url": public_url,
            "animal_detected": animal,
            "confidence_score": float(confidence),
            "user_id": user_id
        }

        supabase.table("labeled_images").insert(label_data).execute()

        return jsonify({
            "status": "saved",
            "image_url": public_url
        }), 200

    except Exception as e:
        print("Save history error:", e)
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
