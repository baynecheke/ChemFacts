import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- Configuration ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")

# --- Flask App Setup ---
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app) 

# --- AI Model Setup ---
STATS_PROMPT = """
You are a "Chemical Stats" generator for a game. A user will provide a
chemical element symbol (like 'Fe') or a formula (like 'H2O').
Your task is to return a JSON object with "gamified" stats for it.

RULES:
1.  **Query Type**: Determine if the query is a single 'element' or a 'molecule'.
2.  **Stats**: Provide ratings from 0 to 10 for each stat.
    - `stability`: 0 = falls apart, 10 = extremely stable (like N2).
    - `reactivity`: 0 = inert (like He), 10 = extremely reactive (like Fluorine or Sodium).
    - `explosiveness`: 0 = not explosive (like H2O), 10 = highly explosive (like TNT or Nitroglycerin).
3.  **Description**: Write a short, engaging description (1-2 sentences).
4.  **Fun Fact**: Provide a one-sentence fun fact.

Respond *only* with the JSON object.
"""

STATS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": { "type": "STRING", "description": "Common name, e.g., 'Water' or 'Iron'" },
        "query_type": { "type": "STRING", "description": "'element' or 'molecule'" },
        "description": { "type": "STRING", "description": "A 1-2 sentence cool description." },
        "stability": { "type": "INTEGER", "description": "Rating 0-10" },
        "reactivity": { "type": "INTEGER", "description": "Rating 0-10" },
        "explosiveness": { "type": "INTEGER", "description": "Rating 0-10" },
        "fun_fact": { "type": "STRING", "description": "A one-sentence fun fact." }
    },
    "required": ["name", "query_type", "description", "stability", "reactivity", "explosiveness", "fun_fact"]
}

stats_model = genai.GenerativeModel(
    'gemini-2.5-flash-preview-09-2025',
    system_instruction=STATS_PROMPT
)

stats_generation_config = genai.GenerationConfig(
    response_mime_type="application/json",
    response_schema=STATS_SCHEMA
)

# --- Frontend Route ---
@app.route('/')
def serve_frontend():
    # This serves the index.html file from the 'static' folder
    return send_from_directory(app.static_folder, 'index.html')

# --- API Endpoint: Get Stats (Rewritten to use AI) ---
@app.route('/api/get_stats', methods=['POST']) # Changed back to POST
def get_stats():
    if not API_KEY:
        return jsonify({"error": "Server is missing GEMINI_API_KEY"}), 500
    
    # Get the query from the JSON body
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Invalid request: 'query' missing in JSON body"}), 400
    
    user_query = data['query']

    try:
        # Call the Gemini AI model
        response = stats_model.generate_content(
            f"Generate stats for: {user_query}",
            generation_config=stats_generation_config
        )
        
        stats_text = response.candidates[0].content.parts[0].text
        return jsonify(json.loads(stats_text))
        
    except Exception as e:
        print(f"An error occurred calling the Gemini API for stats: {e}")
        return jsonify({"error": f"AI stats generation failed: {e}"}), 500

# --- Run the Server ---
if __name__ == '__main__':
    print("Starting Python Flask server for Chem Stats (AI Mode)...")
    if not os.path.exists('static'):
        os.makedirs('static')
    print("Remember to put your index.html file in the 'static' folder.")
    app.run(port=5001, debug=True)