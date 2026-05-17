from django.urls import path
from . import views

urlpatterns = [
    path('', views.collaborate_home, name='collaborate_home'),
    path('room/<int:group_id>/', views.collaborate_room, name='collaborate_room'),
    path('send/<int:room_id>/', views.send_message, name='send_message'),
    path('messages/<int:room_id>/', views.get_messages, name='get_messages'),
    path('toggle-video/<int:room_id>/', views.toggle_video, name='toggle_video'),
    path('toggle-screen/<int:room_id>/', views.toggle_screen_share, name='toggle_screen_share'),
    path('share-resource/<int:room_id>/', views.share_resource, name='share_resource'),
]
