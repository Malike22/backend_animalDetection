import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
MODEL_URL = os.getenv('MODEL_URL')

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def query_huggingface(image_url):
    """Send image URL to Hugging Face Inference API"""
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    # Download image first
    try:
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            return None, f"Failed to download image: {image_response.status_code}"
        
        # Call Hugging Face API
        response = requests.post(MODEL_URL, headers=headers, data=image_response.content)
        
        if response.status_code != 200:
            return None, f"Hugging Face API error: {response.text}"
            
        return response.json(), None
    except Exception as e:
        return None, str(e)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook/process-image', methods=['POST'])
def process_image():
    """Webhook triggered by Supabase when a new image is uploaded"""
    data = request.json
    image_url = data.get('image_url')
    captured_image_id = data.get('captured_image_id')
    user_id = data.get('user_id')

    if not all([image_url, captured_image_id, user_id]):
        return jsonify({"error": "Missing parameters"}), 400

    # 1. Update status to 'processing'
    supabase.table('captured_images').update({
        'status': 'processing'
    }).eq('id', captured_image_id).execute()

    # 2. Get Prediction from Hugging Face
    prediction, error = query_huggingface(image_url)
    
    if error:
        supabase.table('captured_images').update({
            'status': 'failed',
            'metadata': {'error': error}
        }).eq('id', captured_image_id).execute()
        return jsonify({"error": error}), 500

    # Hugging Face usually returns a list of labels
    try:
        if isinstance(prediction, list) and len(prediction) > 0:
            top_result = prediction[0]
            animal_name = top_result.get('label', 'Unknown')
            confidence = top_result.get('score', 0) * 100
        else:
            animal_name = "Unknown"
            confidence = 0
    except Exception as e:
        print(f"Prediction parsing error: {e}")
        animal_name = "Error"
        confidence = 0

    # 3. Insert into labeled_images
    supabase.table('labeled_images').insert({
        'captured_image_id': captured_image_id,
        'user_id': user_id,
        'labeled_image_url': image_url,
        'animal_detected': animal_name,
        'confidence_score': confidence
    }).execute()

    # 4. Update status in captured_images to 'completed'
    supabase.table('captured_images').update({
        'status': 'completed'
    }).eq('id', captured_image_id).execute()

    return jsonify({
        "status": "success",
        "animal": animal_name,
        "confidence": confidence
    }), 200

if __name__ == '__main__':
    # For local testing, host on 0.0.0.0 and use a configurable port
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
