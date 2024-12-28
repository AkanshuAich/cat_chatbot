import os
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
# import openai
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# ======================================================
# 1. Configure Keys
# ======================================================
#
# In production, do NOT hardcode keys; load them via environment variables or secure vault.
# But for demonstration, you can paste them here.

# (1) Temporary OpenAI key for "gpt-4o-mini" usage
client = OpenAI()
# (2) TheCatAPI key
#    You can keep it in an environment variable named "CAT_API_KEY" (recommended)
#    or replace it with your actual key here for local testing.
CAT_API_KEY = os.getenv("CAT_API_KEY")

# Model to use (per your prompt)
OPENAI_MODEL = "gpt-4o-mini"


# ======================================================
# 2. Define the Cat API function schema for OpenAI
# ======================================================
# This is how we inform GPT about a function it can call.
cat_function = {
    "name": "get_cat_images",
    "description": "Retrieve cat images from TheCatAPI, optionally filtered by breed and number of images.",
    "parameters": {
        "type": "object",
        "properties": {
            "breed": {
                "type": "string",
                "description": "Breed ID of cat (e.g. 'beng' for Bengal). Leave blank for random cats."
            },
            "count": {
                "type": "integer",
                "description": "How many cat images to retrieve (1-100). Defaults to 1.",
                "default": 1
            }
        },
        "required": []
    },
}


# ======================================================
# 3. The Actual Function That Calls TheCatAPI
# ======================================================
def call_cat_api(breed=None, count=1):
    """
    Calls TheCatAPI to retrieve cat images.
    For breed IDs, see https://api.thecatapi.com/v1/breeds for a list of possible IDs.
    For more than 10 images or breed filters, you must pass a valid Cat API key.
    """
    url = "https://api.thecatapi.com/v1/images/search"
    params = {
        "limit": count
    }
    # If a breed was specified, add it to the parameters
    if breed:
        params["breed_ids"] = breed

    # Prepare headers with your Cat API Key
    headers = {
        "x-api-key": CAT_API_KEY
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # In production, handle errors properly and return a helpful message or status code
        print(f"Error calling TheCatAPI: {e}")
        return []

    # Extract just the 'url' fields, though you could also return full data
    images = [item["url"] for item in data]
    return images


# ======================================================
# 4. /chat Endpoint
# ======================================================
@app.route('/chat', methods=['POST'])
def chat():
    """
    Main endpoint that:
      - Receives user messages in JSON ({"message": "..."}).
      - Sends them to OpenAI ChatCompletion with the cat function definition.
      - If a function_call is requested by GPT, calls `call_cat_api`.
      - Returns a JSON response with either text or cat images.
    """
    # Extract user input from POST JSON
    user_input = request.json.get("message", "")
    print("User Input:", user_input)

    # 1) Send the user’s message to the OpenAI Chat Completion
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": user_input}],
            functions=[cat_function],    # We define the get_cat_images function for GPT
            function_call="auto",        # Let GPT decide when to use the function
        )
        print("GPT Response:", response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # 2) Check if GPT wants to call the function
    message = response.choices[0].message
    if message.function_call:
        # The model is requesting a function call
        function_name = message.function_call.name
        arguments_json = message.function_call.arguments  # JSON string
        function_args = json.loads(arguments_json)

        if function_name == "get_cat_images":
            # Parse arguments
            breed = function_args.get("breed")
            count = function_args.get("count", 1)

            # Actually call the CatAPI
            cat_images = call_cat_api(breed, count)

            # Return the result in JSON
            # You can optionally feed this back to GPT for a fancy formatted reply,
            # but here we’ll just return the raw images in a JSON response.
            return jsonify({
                "role": "assistant",
                "content": f"Here are {len(cat_images)} cat images for breed '{breed or 'random'}':",
                "images": cat_images
            })

    # 3) Otherwise, GPT just responded with normal text. Return that.
    return jsonify({
        "role": "assistant",
        "content": message.get("content", "")
    })


# ======================================================
# 5. Optional Root Endpoint
# ======================================================
@app.route('/', methods=['GET'])
def index():
    return "Flask backend for OpenAI + TheCatAPI is up and running!"


# ======================================================
# 6. Run the Flask App
# ======================================================
# For local dev usage you can do: python app.py
# For production, run via WSGI server (e.g. gunicorn).
if __name__ == '__main__':
    # Enable CORS for all endpoints
    CORS(app)
    # Note: Use debug=True only during development
    app.run(host='0.0.0.0', port=5000, debug=True)
