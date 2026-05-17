from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from .models import Room, Message, SharedResource
from groups.models import StudyGroup
import json

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def collaborate_home(request):
    user_groups = request.user.study_groups.all()
    rooms = Room.objects.filter(group__in=user_groups, is_active=True)
    
    query = request.GET.get('q', '')
    if query:
        rooms = rooms.filter(name__icontains=query) | rooms.filter(group__name__icontains=query) | rooms.filter(group__subject__icontains=query)
    
    return render(request, 'collaborate/home.html', {'rooms': rooms, 'query': query})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def collaborate_room(request, group_id):
    group = get_object_or_404(StudyGroup, pk=group_id)
    
    if request.user not in group.members.all():
        return redirect('group_list')
    
    room, created = Room.objects.get_or_create(
        group=group,
        defaults={'name': f"{group.name} - Collaboration Space"}
    )
    
    # User requested to stop showing chat history - start fresh for each session
    messages = [] 
    resources = room.resources.all().order_by('-timestamp')
    
    # Get current max ID so sync() only fetches messages sent AFTER joining
    latest_msg = room.messages.order_by('-id').first()
    max_id = latest_msg.id if latest_msg else 0
    
    return render(request, 'collaborate/room.html', {
        'room': room,
        'group': group,
        'messages': messages,
        'resources': resources,
        'max_id': max_id
    })

@login_required
def share_resource(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        title = request.POST.get('title')
        link = request.POST.get('link')
        file = request.FILES.get('file')
        
        if title and (link or file):
            SharedResource.objects.create(
                room=room,
                sender=request.user,
                title=title,
                link=link,
                file=file
            )
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        data = json.loads(request.body)
        content = data.get('content', '')
        
        if content:
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content
            )
            return JsonResponse({
                'success': True,
                'message': {
                    'sender': message.sender.username,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%H:%M')
                }
            })
    return JsonResponse({'success': False})

@login_required
def toggle_video(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        room.video_active = not room.video_active
        if room.video_active:
            room.video_started_by = request.user
        else:
            room.video_started_by = None
        room.save()
        return JsonResponse({'success': True, 'video_active': room.video_active})
    return JsonResponse({'success': False})

@login_required
def toggle_screen_share(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        room.screen_sharing_active = not room.screen_sharing_active
        if room.screen_sharing_active:
            room.screen_shared_by = request.user
        else:
            room.screen_shared_by = None
        room.save()
        return JsonResponse({'success': True, 'screen_sharing_active': room.screen_sharing_active})
    return JsonResponse({'success': False})

@login_required
def get_messages(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    try:
        last_id = int(request.GET.get('last_id', 0))
        new_messages = room.messages.filter(id__gt=last_id).order_by('timestamp')
        messages_data = [{
            'id': msg.id,
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        } for msg in new_messages]
        
        resources = room.resources.all().order_by('-timestamp')[:5]
        resources_data = []
        for r in resources:
            try:
                res_url = r.file.url if r.file else r.link
                resources_data.append({
                    'title': r.title,
                    'url': res_url,
                    'sender': r.sender.username,
                    'is_file': bool(r.file)
                })
            except: continue
        
        return JsonResponse({
            'messages': messages_data,
            'resources': resources_data,
            'video_active': room.video_active,
            'video_started_by': room.video_started_by.username if room.video_started_by else None,
            'screen_active': room.screen_sharing_active,
            'screen_shared_by': room.screen_shared_by.username if room.screen_shared_by else None,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
