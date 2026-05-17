from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from groups.models import StudyGroup
from doubts.models import PeerDoubt

def home(request):
    return render(request, 'core/home.html')


