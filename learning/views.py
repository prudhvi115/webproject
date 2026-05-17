from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import LearningPath, Resource, UserProgress, CourseSchedule, WeeklyContent
from django.conf import settings
import requests
import json

@login_required
def path_list(request):
    paths = LearningPath.objects.all()
    user = request.user
    
    # Recommendation
    recommended = []
    if user.learning_style:
        # Just a simple check if any resource in path matches style would be complex, 
        # let's recommend based on difficulty for now.
        pass

    return render(request, 'learning/path_list.html', {'paths': paths})

@login_required
def path_detail(request, pk):
    path = get_object_or_404(LearningPath, pk=pk)
    resources = path.resources.all()
    completed_resources = UserProgress.objects.filter(user=request.user, resource__in=resources).values_list('resource_id', flat=True)
    
    progress_percent = 0
    if resources.count() > 0:
        progress_percent = int((len(completed_resources) / resources.count()) * 100)

    return render(request, 'learning/path_detail.html', {
        'path': path, 
        'resources': resources,
        'completed_ids': list(completed_resources),
        'progress': progress_percent
    })

@login_required
def complete_resource(request, resource_id):
    if request.method == 'POST':
        resource = get_object_or_404(Resource, pk=resource_id)
        UserProgress.objects.get_or_create(user=request.user, resource=resource)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def view_schedule(request):
    schedule, created = CourseSchedule.objects.get_or_create(user=request.user)
    if created and hasattr(request.user, 'interests') and request.user.interests:
        schedule.subject = request.user.interests
        schedule.save()
    
    # Check if content exists for current week
    try:
        content = WeeklyContent.objects.get(schedule=schedule, week_number=schedule.current_week)
        # If previous generation failed, delete and retry
        if content.title == "Error":
            content.delete()
            raise WeeklyContent.DoesNotExist
    except WeeklyContent.DoesNotExist:
        # Generate content using AI
        try:
            import requests
            import json
            
            week_num = schedule.current_week
            subject = schedule.subject
            
            system_instruction = f"You are an academic course planner. Create a detailed weekly schedule for Week {week_num} of a 16-week course on '{subject}'. The output should be valid Markdown with clear headings for 'Day 1' to 'Day 7', topics, and subtopics. Do not include introductory text, just the schedule content."
            
            payload = {
                "contents": [{
                    "parts": [{"text": system_instruction}]
                }]
            }
            
            headers = {'Content-Type': 'application/json'}
            API_KEY = settings.GEMINI_API_KEY
            
            models_to_try = [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.0-flash-lite",
                "gemini-2.0-flash",
                "gemini-flash-latest",
            ]
            
            generated_text = "Schedule generation failed. Please try again later."
            
            from core.utils import make_gemini_request
            
            if API_KEY:
                for model in models_to_try:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
                        
                        # Use robust request
                        response = make_gemini_request(url, payload, headers, timeout=30)
                        
                        if response.status_code == 200:
                            data = response.json()
                            generated_text = data['candidates'][0]['content']['parts'][0]['text']
                            break
                    except Exception:
                        continue
            
            content = WeeklyContent.objects.create(
                schedule=schedule,
                week_number=week_num,
                title=f"Week {week_num}: {subject} Concepts",
                content=generated_text
            )
            
        except Exception as e:
            content = WeeklyContent(week_number=week_num, title="Error", content=f"Could not generate schedule: {str(e)}")

    return render(request, 'learning/schedule.html', {'schedule': schedule, 'weekly_content': content})

@login_required
def complete_week(request):
    if request.method == 'POST':
        schedule = get_object_or_404(CourseSchedule, user=request.user)
        
        # Logic: 1 -> 2 -> ... -> 16 -> 1
        if schedule.current_week >= 16:
            schedule.current_week = 1
        else:
            schedule.current_week += 1
            
        schedule.save()
        return redirect('view_schedule')
        
    return redirect('view_schedule')
