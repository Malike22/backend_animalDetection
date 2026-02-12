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
MODEL_URL = os.getenv("MODEL_URL")  # Example: https://xxxx.hf.space/predict

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not MODEL_URL:
    raise Exception("Missing required environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =========================
# MODEL CALL
# =========================
def query_model(image_url):
    """
    Downloads the image and sends it to the model URL.
    Returns (prediction_dict, error_str)
    """
    try:
        print("Downloading image:", image_url)
        resp = requests.get(image_url, timeout=20)
        resp.raise_for_status()

        files = {"image": ("image.jpg", resp.content, "image/jpeg")}

        print("Sending to model:", MODEL_URL)
        response = requests.post(MODEL_URL, files=files, timeout=60)
        response.raise_for_status()

        try:
            result = response.json()
        except ValueError:
            return None, f"Model returned invalid JSON: {response.text[:200]}"

        return result, None

    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"
    except Exception as e:
        return None, str(e)

# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

# =========================
# WEBHOOK
# =========================
@app.route("/webhook/process-image", methods=["POST"])
def process_image():
    try:
        data = request.get_json(force=True)
        image_url = data.get("image_url")
        captured_image_id = data.get("captured_image_id")
        user_id = data.get("user_id")

        if not all([image_url, captured_image_id, user_id]):
            return jsonify({"error": "Missing parameters"}), 400

        print("Processing captured_image_id:", captured_image_id)

        # Update → processing
        supabase.table("captured_images").update({
            "status": "processing"
        }).eq("id", captured_image_id).execute()

        # Call model
        prediction, error = query_model(image_url)
        if error:
            print("Model error:", error)
            supabase.table("captured_images").update({
                "status": "failed",
                "metadata": str(error)  # Safe if column is text
            }).eq("id", captured_image_id).execute()
            return jsonify({"error": error}), 500

        # Safe parsing
        animal_name = prediction.get("label", "unknown")
        try:
            confidence = float(prediction.get("confidence", 0)) * 100
        except Exception:
            confidence = 0

        # Insert result
        supabase.table("labeled_images").insert({
            "captured_image_id": captured_image_id,
            "user_id": user_id,
            "labeled_image_url": image_url,
            "animal_detected": animal_name,
            "confidence_score": confidence
        }).execute()

        # Update → completed
        supabase.table("captured_images").update({
            "status": "completed"
        }).eq("id", captured_image_id).execute()

        return jsonify({
            "status": "success",
            "animal": animal_name,
            "confidence": confidence
        }), 200

    except Exception as e:
        # FATAL ERROR: log full stacktrace for debugging
        import traceback
        print("FATAL ERROR:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
