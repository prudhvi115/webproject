import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("No API Key found")
    exit()

# List models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
try:
    response = requests.get(url)
    if response.status_code == 200:
        print("Available Models:")
        models = response.json().get('models', [])
        for m in models:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(f"- {m['name']} ({m['version']})")
    else:
        print(f"Error listing models: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")

# Test Generation with 1.5 Flash
print("\nTesting Generation with gemini-flash-latest...")
gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
payload = {
    "contents": [{"parts": [{"text": "Hello, are you working?"}]}]
}
headers = {'Content-Type': 'application/json'}
try:
    response = requests.post(gen_url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Generation Error: {e}")
