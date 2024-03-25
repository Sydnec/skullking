# myapp/views/game.py

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from myapp.models import Room
from myapp.views.room import joinroom

@login_required
def game(request, room_id=None):
    room_id = room_id.upper()
    if room_id:
        user = request.user
        try:
            room = Room.objects.get(code=room_id) 
            players = room.players.all()  
        except Room.DoesNotExist:
            return render(request, 'myapp/error.html', {'error': "Room doesn't exist"})
        # Essayer de rejoindre la room (la gestion de s'il est présent se passe dans joinroom)
        if joinroom(request=request, room=room) == -1:
            return render(request, 'myapp/error.html', {'error': "Room is full"})

        players = room.players.all() 
        usernames = [player.user.username for player in players]
        is_owner = room.owner.user == user
        return render(request, 'myapp/room.html', {'room_id': room_id, 'usernames': usernames, 'is_owner': is_owner})
    else:
        return render(request, 'myapp/error.html', {'error': "No room code found"})