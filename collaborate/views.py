from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Room, Message
from groups.models import StudyGroup
import json

@login_required
def collaborate_home(request):
    user_groups = request.user.study_groups.all()
    # Find active rooms for these groups
    rooms = []
    for group in user_groups:
        room, created = Room.objects.get_or_create(group=group, defaults={'name': f"{group.name} Room"})
        rooms.append(room)
    return render(request, 'collaborate/home.html', {'rooms': rooms})

@login_required
def room_view(request, group_id):
    group = get_object_or_404(StudyGroup, pk=group_id)
    if request.user not in group.members.all():
        return redirect('dashboard')
    
    room, created = Room.objects.get_or_create(group=group, defaults={'name': f"{group.name} Room"})
    return render(request, 'collaborate/room.html', {'room': room, 'group': group})

@login_required
def get_messages(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    # Check if user is in the group of the room
    if request.user not in room.group.members.all():
         return JsonResponse({'error': 'Unauthorized'}, status=403)
         
    last_id = request.GET.get('last_id', 0)
    messages = Message.objects.filter(room=room, id__gt=last_id).order_by('timestamp')
    
    data = [{
        'id': msg.id,
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M')
    } for msg in messages]
    
    return JsonResponse({'messages': data})

@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        if request.user not in room.group.members.all():
             return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        content = data.get('content')
        if content:
            msg = Message.objects.create(room=room, sender=request.user, content=content)
            return JsonResponse({'status': 'ok', 'id': msg.id})
            
    return JsonResponse({'error': 'Invaild request'}, status=400)
