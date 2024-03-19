from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        return render(request, 'myapp/home.html')
    else:
        return redirect('login')