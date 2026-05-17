import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(API_URL)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        for m in models.get('models', []):
            print(m.get('name'))
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
