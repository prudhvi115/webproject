from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import requests

API_KEY = "AIzaSyBqG0TWFfwzS6d_FgIZTHmtJEszh5AhVC4"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"

def chat_view(request):
    return render(request, 'doubt_ai/chat.html')

@login_required
def ask_ai(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            
            payload = {
                "contents": [{
                    "parts": [{"text": user_message}]
                }]
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                # Extract text from Gemini response structure
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                return JsonResponse({'message': ai_text})
            else:
                return JsonResponse({'error': 'Failed to get response from AI'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)
