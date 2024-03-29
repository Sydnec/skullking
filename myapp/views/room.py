# myapp/views/room.py

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from myapp.models.models import Room, Player, Hand
from myapp.views.error import error
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required
def newRoom(request):
    user = request.user
    player = Player.objects.create(user=user)
    room = Room.objects.create(owner=user)
    sendRoomUpdates(room, "create")
    return redirect('/room/'+room.code)

@login_required
def joinRoom(request, room):
    user = request.user
    if room:
        if not room.players.filter(user=user).exists():
            if room.players.count() < 8:
                player = Player.objects.create(user=user)
                room.players.add(player)
                Hand.objects.create(player=player)
                sendRoomUpdates(room, "join")
                return 1
            else: 
                return -1
        else:
            return 0
    else:
        return error(request, "Room not found")

@login_required
def leaveRoom(request, room_id):
    if room_id:
        user = request.user
        room = Room.objects.get(code=room_id)
        if room.owner == user:
            players_in_room = Player.objects.filter(rooms=room)
            for player in players_in_room:
                player.delete()
            sendRoomUpdates(room, "delete")
            room.delete()
        else:
            player = Player.objects.get(user=user, rooms=room)
            room.players.remove(player)
            player.delete()
            sendRoomUpdates(room, "leave")
        return redirect('/')
    else:
        return 

def sendRoomUpdates(room, message):
    channel_layer = get_channel_layer()
    usernames = [player.user.username for player in room.players.all()]
    data = {
        'code': room.code,
        'usernames': usernames,
        'message': message
    }
    async_to_sync(channel_layer.group_send)(
        'update_room_group',
        {
            'type': 'update.rooms',
            'data': data
        }
    )