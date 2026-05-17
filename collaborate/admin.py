from django.contrib import admin
from .models import Room, Message

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'is_active', 'video_active', 'screen_sharing_active', 'created_at']
    list_filter = ['is_active', 'video_active', 'screen_sharing_active']
    search_fields = ['name', 'group__name']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'content', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['sender__username', 'content']
