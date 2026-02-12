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
# CONFIGURATION
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MODEL_URL = os.getenv("MODEL_URL")  # HF Docker Space endpoint

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not MODEL_URL:
    raise Exception("Missing required environment variables.")

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# =========================
# SEND IMAGE TO DOCKER SPACE
# =========================
def query_model(image_url):
    try:
        # 1️⃣ Download image from Supabase storage
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            return None, f"Failed to download image: {image_response.status_code}"

        # 2️⃣ Send as file (multipart/form-data)
        files = {
            "image": ("image.jpg", image_response.content, "image/jpeg")
        }

        response = requests.post(
            MODEL_URL,
            files=files,
            timeout=60
        )

        if response.status_code != 200:
            return None, response.text

        return response.json(), None

    except Exception as e:
        return None, str(e)


# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


# =========================
# WEBHOOK ENDPOINT
# =========================
@app.route("/webhook/process-image", methods=["POST"])
def process_image():

    data = request.json

    image_url = data.get("image_url")
    captured_image_id = data.get("captured_image_id")
    user_id = data.get("user_id")

    if not all([image_url, captured_image_id, user_id]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        # 1️⃣ Update status → processing
        supabase.table("captured_images").update({
            "status": "processing"
        }).eq("id", captured_image_id).execute()

        # 2️⃣ Call model
        prediction, error = query_model(image_url)

        if error:
            supabase.table("captured_images").update({
                "status": "failed",
                "metadata": {"error": error}
            }).eq("id", captured_image_id).execute()

            return jsonify({"error": error}), 500

        # 3️⃣ Parse prediction response
        animal_name = prediction.get("label", "Unknown")
        confidence = float(prediction.get("confidence", 0)) * 100

        # 4️⃣ Insert into labeled_images table
        supabase.table("labeled_images").insert({
            "captured_image_id": captured_image_id,
            "user_id": user_id,
            "labeled_image_url": image_url,
            "animal_detected": animal_name,
            "confidence_score": confidence
        }).execute()

        # 5️⃣ Update status → completed
        supabase.table("captured_images").update({
            "status": "completed"
        }).eq("id", captured_image_id).execute()

        return jsonify({
            "status": "success",
            "animal": animal_name,
            "confidence": confidence
        }), 200

    except Exception as e:
        supabase.table("captured_images").update({
            "status": "failed",
            "metadata": {"error": str(e)}
        }).eq("id", captured_image_id).execute()

        return jsonify({"error": str(e)}), 500


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
