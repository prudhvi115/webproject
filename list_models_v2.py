import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("No API Key found")
    exit()

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        with open('available_models.json', 'w') as f:
            json.dump(models, f, indent=2)
        print("Models saved to available_models.json")
    else:
        print(f"Error: {response.status_code} {response.text}")
except Exception as e:
    print(f"Error: {e}")
