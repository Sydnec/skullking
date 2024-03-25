# myapp/views/room.py

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from myapp.models.models import Room, Player
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def room_redirect(request):
    content = request.GET.get('content', '').upper()
    return redirect(f'/room/{content}')

@login_required
def newroom(request):
    user = request.user
    player = Player.objects.create(user=user)
    room = Room.objects.create(owner=player) 
    room.players.add(player)
    send_room_updates(room, "create")
    return redirect('/room/'+room.code)

@login_required
def joinroom(request, room=None):
    user = request.user
    if room:
        if not room.players.filter(user=user).exists():
            if room.players.count() < 8:
                player = Player.objects.create(user=user)
                room.players.add(player)
                send_room_updates(room, "join")
                return 1
            else: 
                return -1
        else:
            return 0
    else:
        return render(request, 'myapp/error.html', {'error': "Room not found"})

@login_required
def leaveroom(request, room_id=None):
    if room_id:
        user = request.user
        room = Room.objects.get(code=room_id)
        player = Player.objects.get(user=user, rooms=room)        
        if room.owner == player:
            players_in_room = Player.objects.filter(rooms=room)
            for player in players_in_room:
                player.delete()
            send_room_updates(room, "delete")
            room.delete()
        else:
            room.players.remove(player)
            player.delete()
            send_room_updates(room, "leave")
        return redirect('/')
    else:
        return render(request, 'myapp/error.html', {'error': 'Room not found'})

def send_room_updates(room, message):
    channel_layer = get_channel_layer()
    usernames = [player.user.username for player in room.players.all()]
    data = {
        'code': room.code,
        'usernames': usernames,
        'message': message
    }
    async_to_sync(channel_layer.group_send)(
        'room_updates',
        {
            'type': 'update.rooms',
            'data': data
        }
    )