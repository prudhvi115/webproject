import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_platform.settings')
django.setup()

from collaborate.models import Room, Message, SharedResource

print("--- Room Stats ---")
for room in Room.objects.all():
    msg_count = room.messages.count()
    res_count = room.resources.count()
    print(f"Room: {room.name} (ID: {room.id})")
    print(f"  Messages: {msg_count}")
    print(f"  Resources: {res_count}")
    print(f"  Video Active: {room.video_active} (Started by: {room.video_started_by})")
    print(f"  Screen Active: {room.screen_sharing_active} (Shared by: {room.screen_shared_by})")
