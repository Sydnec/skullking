# myapp/views/home.py

from django.shortcuts import render
from django.contrib.auth.models import User
from myapp.models.models import Room, Player

def display_home(request):
    return render(request, 'myapp/home.html')

def display_rooms(request):
    rooms = Room.objects.exclude(rounds__isnull=False)
    room_data = []
    for room in rooms:
        players = room.players.all()
        room_usernames = [player.user.username for player in players]
        room_data.append({'code': room.code, 'usernames': room_usernames})
    return render(request, 'myapp/rooms.html', {'rooms_data': room_data})