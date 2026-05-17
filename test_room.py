#!/usr/bin/env python
"""Test script to verify collaborate room functionality"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_platform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from groups.models import StudyGroup
from collaborate.models import Room

User = get_user_model()

# Create test client
client = Client()

# Get or create a test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✓ Created test user: {user.username}")
else:
    print(f"✓ Using existing user: {user.username}")

# Login
logged_in = client.login(username='testuser', password='testpass123')
print(f"✓ Login successful: {logged_in}")

# Get or create a study group
group = StudyGroup.objects.first()
if not group:
    group = StudyGroup.objects.create(
        name="Test Study Group",
        subject="Computer Science",
        description="Test group for collaboration"
    )
    group.members.add(user)
    print(f"✓ Created test group: {group.name}")
else:
    if user not in group.members.all():
        group.members.add(user)
    print(f"✓ Using existing group: {group.name}")

# Test the collaborate room URL
print(f"\n🧪 Testing collaborate room URL...")
response = client.get(f'/collaborate/room/{group.id}/')
print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    print("   ✅ SUCCESS! Room loaded without errors")
    
    # Check if the room was created
    room = Room.objects.filter(group=group).first()
    if room:
        print(f"   ✓ Room created: {room.name}")
        print(f"   ✓ Room ID: {room.id}")
    
    # Test the get_messages endpoint
    if room:
        msg_response = client.get(f'/collaborate/messages/{room.id}/')
        print(f"\n🧪 Testing get_messages endpoint...")
        print(f"   Status Code: {msg_response.status_code}")
        if msg_response.status_code == 200:
            print("   ✅ SUCCESS! Messages endpoint working")
            import json
            data = json.loads(msg_response.content)
            print(f"   ✓ Messages: {len(data['messages'])}")
            print(f"   ✓ Video active: {data['video_active']}")
            print(f"   ✓ Screen sharing active: {data['screen_active']}")
        else:
            print(f"   ❌ FAILED! Status: {msg_response.status_code}")
else:
    print(f"   ❌ FAILED! Status: {response.status_code}")
    if hasattr(response, 'content'):
        print(f"   Error: {response.content[:500]}")

print("\n" + "="*50)
print("Test complete!")
