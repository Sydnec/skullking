# myapp/views/room.py

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from myapp.models.models import Room, Player

def room_redirect(request):
    content = request.GET.get('content', '').upper()
    return redirect(f'/room/{content}')

@login_required
def newroom(request):
    # Récupérer l'utilisateur actuel à partir de la requête
    user = request.user
    # Créer un nouveau joueur lié à l'utilisateur actuel
    player = Player.objects.create(user=user)
    # Crée une nouvelle instance de Room
    room = Room.objects.create(owner=player) 
    # Ajouter ce joueur à la salle
    room.players.add(player)
    # Rediriger l'utilisateur vers une autre page ou un template
    return redirect('/room/'+room.code)


@login_required
def joinroom(request, room_id=None):
    # Récupérer l'utilisateur actuel à partir de la requête
    user = request.user
    if room_id:
        try:
            # Récupérer la room correspondant à l'ID fourni
            room = Room.objects.get(code=room_id)
        except Room.DoesNotExist:
            return render(request, 'myapp/error.html', {'error': "Room doesn't exist"})

        # Vérifier si l'utilisateur est déjà dans la salle
        if not room.players.filter(user=user).exists():
            # Créer un nouveau joueur lié à l'utilisateur actuel
            player = Player.objects.create(user=user)
            # Ajouter ce joueur à la salle
            room.players.add(player)
            # Rediriger l'utilisateur vers /room/ + room_id
            return redirect('/room/'+str(room_id))
    else:
        return render(request, 'myapp/error.html', {'error': "Room code not found"})

@login_required
def leaveroom(request, room_id=None):
    if room_id:
        # Obtenez l'utilisateur actuel
        user = request.user
        # Recherchez la salle à partir de laquelle l'utilisateur doit partir
        # Vous devrez adapter cette logique en fonction de votre modèle
        room = Room.objects.get(code=room_id)
        # Supprimez l'utilisateur de la salle
        player = Player.objects.get(user=user, rooms=room)
        if room.owner == player:
            players_in_room = Player.objects.filter(rooms=room)
            # Supprimer chaque joueur associé à la salle
            for player in players_in_room:
                player.delete()
            room.delete()
        return redirect('/')
    else:
        return render(request, 'myapp/error.html', {'error': 'Invalid request method'})