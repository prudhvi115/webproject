import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.utils import timezone
from .models import StudyGroup, UserGroupProgress
from .forms import StudyGroupForm
from django.conf import settings
from django.db.models import Q

# Gemini API Config
API_KEY = settings.GEMINI_API_KEY
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"

def get_ai_recommendations(user, groups):
    """Uses Gemini to find the best matching study groups from the list."""
    if not groups or not user.interests:
        return []
        
    group_data = [{"id": g.id, "name": g.name, "subject": g.subject, "desc": g.description[:100]} for g in groups]
    
    prompt = f"""
    User Interests: {user.interests}
    Learning Style: {user.learning_style}
    
    Available Groups:
    {json.dumps(group_data)}
    
    Identify the top 3 best matching Study Group IDs (comma-separated) for this user. 
    Return ONLY the list of IDs (e.g., 2, 5, 8).
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    API_KEY = settings.GEMINI_API_KEY
    
    # Try multiple models in case of quota or SSL issues
    models_to_try = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-pro-latest"]
    
    for model in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                import re
                ids = [int(i) for i in re.findall(r'\d+', raw_text)]
                return ids
            else:
                print(f"AI Recommendation: {model} returned {response.status_code}")
                
        except Exception as e:
            print(f"AI Recommendation Error with {model}: {str(e)}")
            continue
            
    return []

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def group_list(request):
    query = request.GET.get('q')
    groups = StudyGroup.objects.all().prefetch_related('members')
    
    if query:
        groups = groups.filter(
            Q(name__icontains=query) | 
            Q(subject__icontains=query) | 
            Q(description__icontains=query)
        )
        
    user = request.user
    ai_matched_ids = []
    
    # Try AI recommendation if it's the first visit to the list
    if not query and user.interests:
        # Cache this or do it once per session for performance
        ai_matched_ids = get_ai_recommendations(user, groups[:20]) # Limit to top 20 for AI analysis
        
    recommended_groups = [g for g in groups if g.id in ai_matched_ids]
    
    # Fallback to keyword matching if AI fails or no recommendations
    if not recommended_groups and user.interests:
        user_interests = [i.strip().lower() for i in user.interests.split(',')]
        for group in groups:
            if any(interest in group.subject.lower() or interest in group.name.lower() or interest in group.description.lower() for interest in user_interests):
                if group not in recommended_groups:
                    recommended_groups.append(group)
    
    joined_group_ids = user.study_groups.values_list('id', flat=True)
    
    return render(request, 'groups/group_list.html', {
        'groups': groups, 
        'recommended_groups': recommended_groups[:5], # Show top 5
        'query': query,
        'joined_group_ids': joined_group_ids,
        'ai_powered': len(ai_matched_ids) > 0
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        form = StudyGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            group.members.add(request.user)
            return redirect('group_detail', pk=group.pk)
    else:
        form = StudyGroupForm()
    return render(request, 'groups/create_group.html', {'form': form})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def group_detail(request, pk):
    group = get_object_or_404(StudyGroup.objects.prefetch_related('members'), pk=pk)
    is_member = request.user in group.members.all()
    
    if is_member and not group.ai_schedule:
        generate_group_schedule(group)
    
    progress = None
    if is_member:
        progress, created = UserGroupProgress.objects.get_or_create(user=request.user, group=group)

    processed_schedule = []
    completed_count = 0
    total_days = 7
    if group.ai_schedule:
        total_days = len(group.ai_schedule)
        for item in group.ai_schedule:
            day_num = int(item['day'])
            is_done = progress.is_completed(day_num) if progress else False
            can_play = progress.can_unlock(day_num) if progress else False
            
            if is_done: completed_count += 1
            
            processed_item = item.copy()
            processed_item['status'] = 'completed' if is_done else ('unlocked' if can_play else 'locked')
            processed_schedule.append(processed_item)

    # Scoreboard Logic
    progress_percent = int((completed_count / total_days) * 100) if total_days > 0 else 0
    can_take_test = (completed_count >= total_days)

    return render(request, 'groups/group_detail.html', {
        'group': group, 
        'is_member': is_member,
        'schedule': processed_schedule,
        'progress_percent': progress_percent,
        'completed_count': completed_count,
        'total_days': total_days,
        'can_take_test': can_take_test
    })

@login_required
def complete_day(request, pk, day_num):
    group = get_object_or_404(StudyGroup, pk=pk)
    from django.contrib import messages
    if request.user in group.members.all():
        progress, created = UserGroupProgress.objects.get_or_create(user=request.user, group=group)
        day_num = int(day_num)
        if day_num not in progress.completed_days:
            if progress.can_unlock(day_num):
                # Use list concatenation to ensure JSONField detects the change
                progress.completed_days = list(progress.completed_days) + [day_num]
                progress.save()
                messages.success(request, f"Day {day_num} marked as complete! Well done.")
            else:
                messages.warning(request, f"Please complete Day {day_num - 1} before starting Day {day_num}.")
        else:
            messages.info(request, f"Day {day_num} is already completed.")
    return redirect('group_detail', pk=pk)

def generate_group_schedule(group):
    # Determine week number
    week_num = getattr(group, 'current_week', 1)
    
    prompt = f"""
    Act as a professional Academic Advisor and AI Group Admin for the study group '{group.name}', which is exploring the subject of '{group.subject}'.
    Your goal is to create a high-quality, 7-day learning path for Week {week_num} of a 16-week course.
    
    For each day (Day 1 to Day 7 of this week), provide:
    1. A clear, academic 'topic' name.
    2. Comprehensive 'daily_notes' written in perfect, encouraging English. These notes should explain the core concepts of the day like a helpful teacher.
    3. An estimated 'time' (e.g., '1 hour 30 mins') that reflects the complexity of the task.
    
    Format the output as a strict JSON list of objects:
    [
        {{
            "day": 1,
            "topic": "Week {week_num} Day 1: [Topic Name]",
            "daily_notes": "...",
            "time": "..."
        }},
        ...
    ]
    Ensure the JSON is valid and do not include any conversational filler.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    # Use newer models and fallback
    models_to_try = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash", 
        "gemini-2.0-flash-lite", 
        "gemini-flash-latest"
    ]
    
    from core.utils import make_gemini_request
    
    for model in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            
            # Use robust request
            response = make_gemini_request(url, payload, headers, timeout=25)
            
            if response.status_code == 200:
                result = response.json()
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                
                import re
                json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if json_match:
                    raw_text = json_match.group(0)
                
                group.ai_schedule = json.loads(raw_text)
                group.schedule_last_updated = timezone.now()
                group.save()
                return # Success
        except Exception as e:
            print(f"Schedule Generation Error ({model}): {str(e)}")
            continue

@login_required
def advance_week(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    
    if request.user in group.members.all():
        # Security/Logic Guard: Check if user has actually finished current week
        progress = UserGroupProgress.objects.filter(user=request.user, group=group).first()
        total_days = len(group.ai_schedule) if group.ai_schedule else 7
        completed_days = len(progress.completed_days) if progress else 0
        
        if completed_days < total_days:
            # Not allowed yet
            from django.contrib import messages
            messages.error(request, f"Please complete all {total_days} tasks of Week {group.current_week} before advancing.")
            return redirect('group_detail', pk=pk)

        if group.current_week >= 16:
            group.current_week = 1
        else:
            group.current_week += 1
        
        # Clear old schedule and progress for this group
        group.ai_schedule = None
        group.save()
        
        # Reset progress for all users in this group for the new week
        UserGroupProgress.objects.filter(group=group).update(completed_days=[])
        
        generate_group_schedule(group)
        
    return redirect('group_detail', pk=pk)

@login_required
def join_group(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    if request.user not in group.members.all():
        group.members.add(request.user)
    return redirect('group_detail', pk=pk)

@login_required
def leave_group(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    if request.user in group.members.all():
        group.members.remove(request.user)
    return redirect('group_list')

@login_required
def delete_group(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    if group.creator == request.user:
        group.delete()
    return redirect('group_list')
