import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(API_URL)
    if response.status_code == 200:
        models = response.json()
        for m in models.get('models', []):
            name = m.get('name')
            methods = m.get('supportedGenerationMethods', [])
            print(f"{name} | {methods}")
except Exception as e:
    print(f"Error: {e}")
