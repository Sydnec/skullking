# myapp/views/game.py

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from myapp.models import Room, Player
from myapp.views.room import joinroom
from myapp.views.error import error

@login_required
def game(request, room_id=None):
    room_id = room_id.upper()
    if room_id:
        user = request.user
        try:
            room = Room.objects.get(code=room_id) 
            players = room.players.all()  
        except Room.DoesNotExist:
            return error(request, "Room doesn't exist")

        if room.has_rounds:
            player = Player.objects.get(user=user, rooms=room)     
            if player in room.players.all():
                return render(request, 'myapp/game.html', {'room_id': room_id})
            else:
                return render(request, 'myapp/game.html', {'room_id': room_id})
        else:
            # Essayer de rejoindre la room (la gestion de s'il est présent se passe dans joinroom)
            if joinroom(request=request, room=room) == -1:
                return error(request, "Room is full")

            players = room.players.all() 
            usernames = [player.user.username for player in players]
            is_owner = room.owner.user == user
            return render(request, 'myapp/room.html', {'room_id': room_id, 'usernames': usernames, 'is_owner': is_owner})
    else:
        return error(request, "No room code found")