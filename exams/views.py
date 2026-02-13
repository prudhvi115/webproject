import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Exam, Question, ExamResult
from groups.models import StudyGroup
from django.conf import settings

# Gemini API Config
API_KEY = settings.GEMINI_API_KEY
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"

@login_required
def exam_list(request):
    user_groups = request.user.study_groups.all()
    exams = Exam.objects.filter(group__in=user_groups).order_by('-created_at')
    return render(request, 'exams/exam_list.html', {'exams': exams})

@login_required
def generate_test(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    
    # Prompt for Gemini to generate Notes + 25 Questions with Explanations and Tricks
    prompt = f"""
    Generate a comprehensive weekly study material and test for the subject '{group.subject}'.
    
    Step 1: Provide high-quality study notes summarizing the main topics.
    Step 2: Generate exactly 25 multiple-choice questions. 
            Each question must have 4 options (A, B, C, D).
            For each question, provide:
            - A step-by-step 'explanation' (analysis).
            - A 'trick' or shortcut to solve it in less time.
    
    Return the response ONLY as a JSON object with the following structure:
    {{
        "notes": "string (markdown formatted)",
        "questions": [
            {{
                "text": "question string",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "correct_option": "A|B|C|D",
                "explanation": "...",
                "trick": "..."
            }}
        ]
    }}
    Do not include any other text or markdown markers.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(raw_text)
            
            exam = Exam.objects.create(
                title=f"Weekly Assessment: {group.subject}",
                group=group,
                topic=group.subject,
                weekly_notes=data.get('notes', '')
            )
            
            for q in data.get('questions', []):
                Question.objects.create(
                    exam=exam,
                    text=q['text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                    explanation=q.get('explanation', ''),
                    trick=q.get('trick', '')
                )
            
            return redirect('take_exam', exam_id=exam.id)
        else:
            return render(request, 'exams/error.html', {'error': 'Failed to generate test from AI.'})
    except Exception as e:
        return render(request, 'exams/error.html', {'error': str(e)})

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if ExamResult.objects.filter(user=request.user, exam=exam).exists():
        return redirect('exam_result', exam_id=exam.id)
        
    if request.method == 'POST':
        score = 0
        questions = exam.questions.all()
        breakdown = []
        
        # User submits json with durations for each question
        user_data = json.loads(request.body)
        answers = user_data.get('answers', {})
        total_time = user_data.get('total_time', 0)
        
        for q in questions:
            user_choice = answers.get(str(q.id), {}).get('choice')
            duration = answers.get(str(q.id), {}).get('duration', 0)
            is_correct = user_choice == q.correct_option
            if is_correct:
                score += 2
            
            breakdown.append({
                'question_id': q.id,
                'text': q.text,
                'user_choice': user_choice,
                'correct_choice': q.correct_option,
                'is_correct': is_correct,
                'duration': duration,
                'explanation': q.explanation,
                'trick': q.trick
            })
        
        ExamResult.objects.create(
            user=request.user, 
            exam=exam, 
            score=score,
            time_taken=total_time,
            breakdown=breakdown
        )
        return JsonResponse({'status': 'ok', 'redirect': f'/exams/result/{exam.id}/'})
        
    questions = exam.questions.all()
    return render(request, 'exams/take_exam.html', {'exam': exam, 'questions': questions})

@login_required
def exam_result(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    result = get_object_or_404(ExamResult, user=request.user, exam=exam)
    return render(request, 'exams/result.html', {'exam': exam, 'result': result})
