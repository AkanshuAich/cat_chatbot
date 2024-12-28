import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI()
CAT_API_KEY = os.getenv("CAT_API_KEY")
OPENAI_MODEL = "gpt-4"  # Change this to your actual model

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

def call_cat_api(breed=None, count=1):
    """
    Calls TheCatAPI to retrieve cat images.
    """
    url = "https://api.thecatapi.com/v1/images/search"
    params = {
        "limit": count
    }
    if breed:
        params["breed_ids"] = breed

    headers = {
        "x-api-key": CAT_API_KEY
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error calling TheCatAPI: {e}")
        return []

    images = [item["url"] for item in data]
    return images

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "")
        print("User Input:", user_input)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": user_input}],
            functions=[cat_function],
            function_call="auto",
        )
        
        # Get the message from the response
        message = response.choices[0].message

        # Check if there's a function call
        if message.function_call:
            # Parse function call
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            if function_name == "get_cat_images":
                breed = function_args.get("breed")
                count = function_args.get("count", 1)

                # Call the Cat API
                cat_images = call_cat_api(breed, count)

                return jsonify({
                    "role": "assistant",
                    "content": f"Here are {len(cat_images)} cat images for breed '{breed or 'random'}':",
                    "images": cat_images
                })

        # If no function call, return the content
        return jsonify({
            "role": "assistant",
            "content": message.content or ""  # Access content directly as a property
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            "role": "assistant",
            "content": f"An error occurred: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def index():
    return "Flask backend for OpenAI + TheCatAPI is up and running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)