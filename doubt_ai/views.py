from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.conf import settings
from .models import DoubtHistory

API_KEY = settings.GEMINI_API_KEY
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def chat_view(request):
    try:
        history = DoubtHistory.objects.filter(user=request.user).order_by('timestamp')
    except Exception:
        history = []
    return render(request, 'doubt_ai/chat.html', {'history': history})

@login_required
def clear_history(request):
    DoubtHistory.objects.filter(user=request.user).delete()
    return redirect('doubt_ai_chat')

@login_required
def ask_ai(request):
    if not settings.GEMINI_API_KEY:
        return JsonResponse({'error': 'CRITICAL: No API Key found. Please add GEMINI_API_KEY to your .env file.'}, status=500)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            
            system_instruction = "You are a professional, helpful, and encouraging Academic Tutor. Provide clear, well-structured, and easy-to-understand explanations in perfect English."
            
            payload = {
                "contents": [{
                    "parts": [{"text": f"Instruction: {system_instruction}\n\nStudent Question: {user_message}"}]
                }]
            }
            
            headers = {'Content-Type': 'application/json'}
            API_KEY = settings.GEMINI_API_KEY
            
            # List of models to try in order of preference
            # List of models to try in order of preference
            models_to_try = [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.0-flash-lite",
                "gemini-2.0-flash",
                "gemini-flash-latest",
            ]
            
            last_error = ""
            from core.utils import make_gemini_request
            
            for model in models_to_try:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
                    print(f"Doubt AI: Trying model {model}...")
                    
                    # Use robust utility
                    response = make_gemini_request(url, payload, headers, timeout=45)
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_text = result['candidates'][0]['content']['parts'][0]['text']
                        
                        # Save to history
                        DoubtHistory.objects.create(
                            user=request.user,
                            message=user_message,
                            response=ai_text
                        )
                        return JsonResponse({'message': ai_text})
                    
                    elif response.status_code == 429:
                        print(f"Doubt AI: Model {model} rate limited (429). Trying next...")
                        last_error = "Free API Quota reached for current models. Please wait 60 seconds."
                        continue
                    
                    elif response.status_code == 404:
                        print(f"Doubt AI: Model {model} returned 404. Trying next...")
                        continue
                        
                    else:
                        last_error = f"API Error {response.status_code}: {response.text[:100]}"
                        print(f"Doubt AI: {last_error}")
                        
                except Exception as e:
                    print(f"Doubt AI: Error with {model}: {str(e)}")
                    last_error = str(e)
                    continue
            
            status_code = 429 if "Quota" in last_error else 500
            return JsonResponse({'error': f'AI Service Busy: {last_error}'}, status=status_code)
                
        except Exception as e:
            return JsonResponse({'error': f'Server Error: {str(e)}'}, status=500)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)
