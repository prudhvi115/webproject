import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import StudyGroup, UserGroupProgress
from .forms import StudyGroupForm
from django.conf import settings

# Gemini API Config
API_KEY = settings.GEMINI_API_KEY
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"

@login_required
def group_list(request):
    groups = StudyGroup.objects.all().prefetch_related('members')
    user = request.user
    recommended_groups = []
    if user.interests:
        user_interests = [i.strip().lower() for i in user.interests.split(',')]
        for group in groups:
            if group.subject.lower() in user_interests:
                recommended_groups.append(group)
    return render(request, 'groups/group_list.html', {'groups': groups, 'recommended_groups': recommended_groups})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = StudyGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            group.members.add(request.user)
            return redirect('group_detail', pk=group.pk)
    else:
        form = StudyGroupForm()
    return render(request, 'groups/create_group.html', {'form': form})

@login_required
def group_detail(request, pk):
    group = get_object_or_404(StudyGroup.objects.prefetch_related('members'), pk=pk)
    is_member = request.user in group.members.all()
    
    # Check if AI Schedule needs generation
    if is_member and not group.ai_schedule:
        generate_group_schedule(group)
    
    # Get or create per-user progress
    progress = None
    if is_member:
        progress, created = UserGroupProgress.objects.get_or_create(user=request.user, group=group)

    # Process schedule to add status (completed, locked, unlocked)
    processed_schedule = []
    if group.ai_schedule:
        for item in group.ai_schedule:
            day_num = int(item['day'])
            is_done = progress.is_completed(day_num) if progress else False
            can_play = progress.can_unlock(day_num) if progress else False
            
            processed_item = item.copy()
            processed_item['status'] = 'completed' if is_done else ('unlocked' if can_play else 'locked')
            processed_schedule.append(processed_item)

    return render(request, 'groups/group_detail.html', {
        'group': group, 
        'is_member': is_member,
        'schedule': processed_schedule,
        'progress': progress
    })

@login_required
def complete_day(request, pk, day_num):
    group = get_object_or_404(StudyGroup, pk=pk)
    if request.user in group.members.all():
        progress, created = UserGroupProgress.objects.get_or_create(user=request.user, group=group)
        day_num = int(day_num)
        if day_num not in progress.completed_days:
            # We should only allow completing if it's currently unlocked
            if progress.can_unlock(day_num):
                progress.completed_days.append(day_num)
                progress.save()
    return redirect('group_detail', pk=pk)

def generate_group_schedule(group):
    prompt = f"""
    Act as the AI Group Admin for a study group named '{group.name}' learning '{group.subject}'.
    Schedule a 7-day learning path. For each day, provide:
    1. A focused 'topic'.
    2. 'daily_notes' (markdown formatted) explaining the topic in detail.
    3. Estimated time to complete.
    
    Return the response ONLY as a JSON list of objects:
    [
        {{
            "day": 1,
            "topic": "...",
            "daily_notes": "...",
            "time": "2 hours"
        }},
        ...
    ]
    Do not include any other text or markdown markers.
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            if "```json" in raw_text: raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text: raw_text = raw_text.split("```")[1].split("```")[0].strip()
            group.ai_schedule = json.loads(raw_text)
            group.schedule_last_updated = timezone.now()
            group.save()
    except:
        pass

@login_required
def join_group(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    if request.user not in group.members.all():
        group.members.add(request.user)
    return redirect('group_detail', pk=pk)
