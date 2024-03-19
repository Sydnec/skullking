# myapp/views/game.py

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from myapp.models import Room
from myapp.views.room import joinroom


@login_required
def game(request, room_id=None):
    if room_id:
        user = request.user
        try:
            room = Room.objects.get(code=room_id) # Récupérer la room correspondant à l'ID fourni
            players = room.players.all()  # Récupérer tous les joueurs de la salle
        except Room.DoesNotExist:
            return HttpResponse("Cette salle n'existe pas.")

        # Vérifier si l'utilisateur est déjà dans la salle sinon l'ajoute
        if not room.players.filter(user=user).exists():
            joinroom(request=request, room_id=room_id)

        players = room.players.all()  # Récupérer tous les joueurs de la salle
        usernames = [player.user.username for player in players]  # Liste des noms d'utilisateur
        return render(request, 'myapp/room.html', {'usernames': usernames, 'room_id': room_id})
    else:
        return HttpResponse("L'ID de la salle n'a pas été fourni.")