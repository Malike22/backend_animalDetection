import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MODEL_URL = os.getenv("MODEL_URL")  # HF Space /predict endpoint

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not MODEL_URL:
    raise Exception("Missing required environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


# =========================
# PREDICT FIRST ENDPOINT
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Check file
        if "image" not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400

        file = request.files["image"]
        image_bytes = file.read()

        # =========================
        # STEP 1 — SEND TO MODEL
        # =========================
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}

        model_response = requests.post(
            MODEL_URL,
            files=files,
            timeout=60
        )

        model_response.raise_for_status()

        try:
            prediction = model_response.json()
        except ValueError:
            return jsonify({
                "error": "Model returned invalid JSON",
                "raw": model_response.text[:200]
            }), 500

        animal_name = prediction.get("label", "unknown")

        try:
            confidence = float(prediction.get("confidence", 0)) * 100
        except:
            confidence = 0

        # =========================
        # STEP 2 — UPLOAD IMAGE TO SUPABASE STORAGE
        # =========================
        filename = f"detected_{os.urandom(6).hex()}.jpg"

        supabase.storage.from_("animal-images").upload(
            filename,
            image_bytes,
            {"content-type": "image/jpeg"}
        )

        public_url = supabase.storage.from_("animal-images").get_public_url(filename)

        # =========================
        # STEP 3 — INSERT INTO DATABASE
        # =========================
        supabase.table("labeled_images").insert({
            "labeled_image_url": public_url,
            "animal_detected": animal_name,
            "confidence_score": confidence
        }).execute()

        # =========================
        # RESPONSE
        # =========================
        return jsonify({
            "status": "success",
            "animal": animal_name,
            "confidence": confidence,
            "image_url": public_url
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
