from django.urls import path
from . import views

urlpatterns = [
    path('', views.doubt_list, name='doubt_list'),
    path('<int:pk>/', views.doubt_detail, name='doubt_detail'),
    path('create/', views.create_doubt, name='create_doubt'),
]
