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
            room = Room.objects.get(code=room_id) # Récupérer la room correspondant à l'ID fourni
            players = room.players.all()  # Récupérer tous les joueurs de la salle
        except Room.DoesNotExist:
            return render(request, 'myapp/error.html', {'error': "Room doesn't exist"})
        # Essayer de rejoindre la room (la gestion de s'il est présent se passe dans joinroom)
        joinroom(request=request, room_id=room_id)
        players = room.players.all()  # Récupérer tous les joueurs de la salle
        usernames = [player.user.username for player in players]  # Liste des noms d'utilisateur
        return render(request, 'myapp/room.html', {'usernames': usernames, 'room_id': room_id})
    else:
        return render(request, 'myapp/error.html', {'error': "No room code found"})