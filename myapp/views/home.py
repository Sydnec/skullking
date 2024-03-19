# myapp/views/home.py

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from myapp.models.models import Room, Player

def home(request):
    if request.user.is_authenticated:
        rooms = Room.objects.all()
        room_data = []
        for room in rooms:
            players = room.players.all()
            room_usernames = [player.user.username for player in players]
            room_data.append({'code': room.code, 'usernames': room_usernames})
        return render(request, 'myapp/home.html', {'rooms_data': room_data})
    else:
        return redirect('login')