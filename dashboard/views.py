from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import *
from doubt_ai.models import DoubtHistory
from notes.models import Note
from groups.models import UserGroupProgress
from exams.models import ExamResult

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard(request):
    user = request.user
    # Simplified groups list to prevent potential attribute errors during refactoring
    groups = user.study_groups.all()
    
    # Analytics
    doubts_count = DoubtHistory.objects.filter(user=user).count()
    total_notes = Note.objects.filter(author=user).count()
    
    # Calculate group completion average
    total_completion = 0
    # Average across ALL groups the user is a member of
    user_groups = user.study_groups.all()
    groups_count = user_groups.count()
    
    for group in user_groups:
        if group.ai_schedule:
            try:
                # Try to get existing progress
                p = UserGroupProgress.objects.filter(user=user, group=group).first()
                if p:
                    total_days = len(group.ai_schedule)
                    if total_days > 0:
                        completed = len(p.completed_days)
                        total_completion += (completed / total_days) * 100
                # If no progress object, it's 0% for this group (which is correct)
            except:
                continue
    
    completion_rate = (total_completion / groups_count) if groups_count > 0 else 0
    
    # Performance Analytics
    exam_results = ExamResult.objects.filter(user=user)
    avg_performance = 0
    if exam_results.exists():
        total_score_pct = sum((r.score / (r.total_marks if r.total_marks else 50)) * 100 for r in exam_results)
        avg_performance = total_score_pct / exam_results.count()
        # Progress is a weighted average: 60% completion, 40% performance (or 50/50)
        # Choosing 50/50 for now as it's a simple "increase based on performance"
        avg_completion = int((completion_rate + avg_performance) / 2)
    else:
        avg_completion = int(completion_rate)
    
    context = {
        'user': user,
        'groups': groups,
        'doubts_count': doubts_count,
        'total_notes': total_notes,
        'avg_completion': avg_completion,
        'daily_progress': int(completion_rate),
        'avg_performance': int(avg_performance),
        'recent_groups': groups[:3]
    }
    return render(request, 'dashboard/dashboard.html', context)
