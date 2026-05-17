from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import PeerDoubt, Answer
from django.db.models import Q

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doubt_list(request):
    query = request.GET.get('q')
    doubts = PeerDoubt.objects.all().order_by('-created_at')
    
    if query:
        doubts = doubts.filter(
            Q(title__icontains=query) |
            Q(subject__icontains=query) |
            Q(content__icontains=query)
        )
        
    return render(request, 'doubts/doubt_list.html', {'doubts': doubts, 'query': query})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doubt_detail(request, pk):
    doubt = get_object_or_404(PeerDoubt, pk=pk)
    answers = doubt.answers.all().order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Answer.objects.create(doubt=doubt, author=request.user, content=content)
            return redirect('doubt_detail', pk=pk)
            
    return render(request, 'doubts/doubt_detail.html', {'doubt': doubt, 'answers': answers})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_doubt(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        if title and subject and content:
            PeerDoubt.objects.create(
                title=title,
                subject=subject,
                content=content,
                author=request.user
            )
            return redirect('doubt_list')
            
    return render(request, 'doubts/create_doubt.html')
