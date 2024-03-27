# myapp/views/game.py

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from myapp.models import *
from myapp.views.room import joinroom
from myapp.views.error import error
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
import json
import time

phase = 1 # 1 = bet, 2 = play

@login_required
def display(request, room_id):
    room_id = room_id.upper()
    if room_id:
        user = request.user
        try:
            room = Room.objects.get(code=room_id) 
        except Room.DoesNotExist:
            return error(request, "Room doesn't exist")
        if room.rounds.count() <= 0: # La partie n'a pas encore commencé
            # Essayer de rejoindre la room (la gestion de s'il est présent se passe dans joinroom)
            if joinroom(request=request, room=room) == -1:
                return error(request, "Room is full")

            players = room.players.all()  
            usernames = [player.user.username for player in players]
            is_owner = room.owner == user
            return render(request, 'myapp/room.html', {'room_id': room_id, 'usernames': usernames, 'is_owner': is_owner})
        else: # La partie à commencer, soit t'en fait parti, soit retour home
            if room.players.filter(user=user).exists():
                return game_logic(request, room)
            else:
                return error(request, "Game has already start")
    else:
        return error(request, "No room code found")

def startgame(request, room_id):
    user = request.user
    try:
        room = Room.objects.get(code=room_id) 
        players = room.players.all()  
    except Room.DoesNotExist:
        return error(request, "Room doesn't exist")

    # Envoi de l'update sur websocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'room_updates',
        {
            'type': 'update_rooms',
            'data': 'start'
        }
    )
    return next_round(request, room)

@login_required
def game_logic(request, room):
    user = request.user
    players = room.players.all()
    current_round = room.rounds.all().latest('value')
    current_player = Player.objects.get(user=user, rooms=room)

    user_index = next((i for i, player in enumerate(players) if player == current_player), None)
    if user_index is not None:
        ordered_players = list(players[user_index + 1:]) + list(players[:user_index])

    players_cards_number = {}
    player_bets = {}

    try:
        player_bets[current_player] = Bet.objects.get(round=current_round, player=current_player)
    except Bet.DoesNotExist:
        player_bets[current_player] = None

    for player in ordered_players:
        try:
            players_cards_number[player] = CardAssociation.objects.filter(hand=Hand.objects.get(player=player), trick__isnull=True).count()
        except Bet.DoesNotExist:
            players_cards_number[player] = 0
        try:
            bet = Bet.objects.get(round=current_round, player=player)
            player_bets[player] = bet
        except Bet.DoesNotExist:
            player_bets[player] = None

    hand_cards = CardAssociation.objects.filter(round=current_round, hand=Hand.objects.get(player=current_player), trick__isnull=True)
    try:
        trick = Trick.objects.get(round=current_round)
        phase = 2
        trick_cards = CardAssociation.objects.filter(round=current_round, trick=trick)
    except Trick.DoesNotExist:
        phase = 1
        trick_cards = None

    data = {
        'room_id': room.code,
        'player_bets': player_bets,
        'round_number': current_round.value,
        'hand_cards': hand_cards,
        'trick_cards': trick_cards,
        'players_cards_number':players_cards_number,
        'start_timer': Bet.objects.filter(round=current_round).count() == room.players.all().count(),
    }
    if phase == 1:
        return render(request, 'myapp/bet.html', data)
    elif phase == 2:
        return render(request, 'myapp/table.html', data)

def next_round(request, room):
    # Création du round
    round_count = room.rounds.all().latest('value').value if room.rounds.exists() else 0
    new_round = Round.objects.create(room=room, value=round_count+1)
    room.rounds.add(new_round)
    # Distribution des cartes
    distribute_cards(room)
    return game_logic(request, room)

def distribute_cards(room):
    current_round = room.rounds.all().latest('value')
    cards_per_player = current_round.value + 9
    players = room.players.all()
    deck = CardAssociation.objects.filter(round=current_round)
    
    # Mélanger les cartes
    shuffled_cards = list(deck)
    random.shuffle(shuffled_cards)

    # Distribuer les cartes
    for player in players:
        hand = Hand.objects.filter(player=player).first()
        for i in range(cards_per_player):
            card_association = shuffled_cards.pop()
            card_association.hand = hand
            card_association.save()

def game_action(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        room = Room.objects.get(code=room_id)
        current_round = room.rounds.all().latest('value')
        current_player = Player.objects.get(user=user, rooms=room)
        action = data.get('action')
        if action == "play":
            return play_card(request, room, data)
        elif action == "bet":
            return bet(request, room, data)
        elif action == "game_phase":
            return game_phase(request, room)
        elif action == "bet_phase":
            return bet_phase(request, room)

def game_phase(request, room):
    current_round = room.rounds.all().latest('value')
    Trick.objects.create(round=current_round)
    return game_logic(request, room)

def bet_phase(request, room):
    next_round(request, room)
    return game_logic(request, room)

def play_card(request, room, data):
    user = request.user
    current_player = Player.objects.get(user=user, rooms=room)
    current_round = room.rounds.all().latest('value')
    if Trick.objects.get(round=current_round):
        # Vérifier que le joueur n'a pas encore joué
        if Trick.objects.filter(round=current_round, player=current_player).count() == 0:
            # Vérifier tour de jeu
            card_name = data.get('card_name')
            card_association = CardAssociation.objects.get(round=current_round, card=Card.objects.get(name=card_name))
            card_association.trick = Trick.objects.get(round=current_round)
            card_association.save()
    return game_logic(request, room)

def bet(request, room, data):
    user = request.user
    current_round = room.rounds.all().latest('value')
    bet_value = data.get('bet_value')
    current_player = Player.objects.get(user=user, rooms=room)

    bet = Bet.objects.filter(round=current_round, player=current_player)
    if bet.count() == 0:
        bet = Bet.objects.create(round=current_round, player=current_player)
    else:
        bet = bet.first()
    bet.value = bet_value
    bet.save()
    return game_logic(request, room)