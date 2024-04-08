# myapp/views/home.py

from django.shortcuts import render

def display_home(request):
    return render(request, 'myapp/home.html')

def display_rooms(request):
    return render(request, 'myapp/rooms.html')