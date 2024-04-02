# myapp/views/game.py

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.db.models import Max, Case, When
from myapp.models import *
from myapp.views.room import joinRoom, sendRoomUpdates
from myapp.views.error import error
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
import json
import time

def sendGameUpdate(room, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'update_game_group', 
        {
            'type': 'update_game',
            'room_id': room.code,
            'data': data,
        }
    )

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
            # Essayer de rejoindre la room (la gestion de s'il est présent se passe dans joinRoom)
            if joinRoom(request=request, room=room) == -1:
                return error(request, "Room is full")

            players = room.players.all()  
            usernames = [player.user.username for player in players]
            is_owner = room.owner == user
            return render(request, 'myapp/room.html', {'room_id': room_id, 'usernames': usernames, 'is_owner': is_owner})
        else: # La partie à commencer, soit t'en fait parti, soit retour home
            if room.players.filter(user=user).exists():
                return gameData(request, room)
            else:
                return error(request, "Game has already start")
    else:
        return error(request, "No room code found")

@login_required
def gameData(request, room):
    user = request.user
    players = room.players.all()
    try:
        current_round = room.rounds.all().latest('value')
    except Round.DoesNotExist:
        return error(request, "You can't play alone")
    current_player = Player.objects.get(user=user, rooms=room)
    user_index = next((i for i, player in enumerate(players) if player == current_player), None)
    if user_index is not None:
        ordered_players = [players[user_index]] + list(players[user_index + 1:]) + list(players[:user_index])
    
    players_data={}

    hand_cards = CardAssociation.objects.filter(round=current_round, hand__player=current_player, trick__isnull=True)
    trick_cards_ordered = None
    try:
        trick = Trick.objects.filter(round=current_round).latest('value')
        phase = 2
        trick_cards = CardAssociation.objects.filter(round=current_round, trick=trick)
        # Ordonner les cartes
        cases = [When(hand__player=player, then=index) for index, player in enumerate(getOrderedPlayers(trick))]
        trick_cards_ordered = trick_cards.annotate(
            player_order=Case(*cases, default=len(ordered_players), output_field=models.IntegerField())
        ).order_by('player_order')
        player_turn = playerTurn(trick)
    except Trick.DoesNotExist:
        phase = 1
        trick_cards = None
        if current_round.value > 1:
            last_trick = Trick.objects.get(value=1, round__value=current_round.value-1, round__room= room)
            player_turn = getOrderedPlayers(last_trick)[1]
        else:
            user_index = next((i for i, player in enumerate(players) if player.user == room.owner), None)
            player_turn = players[user_index + 1]

    for player in ordered_players:
        players_data[player] = {
            'cards_number': CardAssociation.objects.filter(hand__player=player, trick__isnull=True, round=current_round).count(),
            'tricks_number': None if phase == 1 else Trick.objects.filter(player=player, round=current_round).count(),
            'your_turn': (player == player_turn)
        }
        try:
            players_data[player]['bet'] = Bet.objects.get(round=current_round, player=player)
        except Bet.DoesNotExist:
            players_data[player]['bet'] = None
    data = {
        'room_id': room.code,
        'round_number': current_round.value,
        'hand_cards': hand_cards,
        'trick_cards': trick_cards_ordered,
        'players_data':players_data,
    }
    if phase == 1:
        return render(request, 'myapp/bet.html', data)
    elif phase == 2:
        return render(request, 'myapp/table.html', data)

def nextRound(room):
    # Création du round
    round_count = room.rounds.all().latest('value').value if room.rounds.exists() else 0
    if round_count == 10:
        return
    else:
        if round_count == 0:
            dealer = Player.objects.get(user=room.owner, rooms=room)
        else:
            last_round = Round.objects.get(room=room, value=round_count)
            ordered_player = getOrderedPlayers(Trick.objects.get(value=1, round=last_round))
            dealer = ordered_player[0]
        new_round = Round.objects.create(room=room, value=round_count+1, player=dealer)
        room.rounds.add(new_round)
        # Distribution des cartes
        distributeCards(room)

def nextTrick(trick_number, current_round):
    if trick_number == current_round.value:
        calculScore(current_round)
        betPhase(current_round.room)
    else:
        time.sleep(2)
        if not Trick.objects.filter(round=current_round, value=trick_number + 1).exists():
            Trick.objects.create(round=current_round, value=trick_number + 1)
            sendGameUpdate(current_round.room, 'next_trick')

def distributeCards(room):
    current_round = room.rounds.all().latest('value')
    cards_per_player = current_round.value
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

def gameAction(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        room = Room.objects.get(code=room_id)
        action = data.get('action')
        if action == "play":
            playCard(request, room, data)
        elif action == "bet":
            bet(request, room, data)
        elif action == "start":
            startGame(room)
        return gameData(request, room)

def startGame(room):
    if 1 < room.players.count() < 8:
        nextRound(room)
        # Envoi de l'update sur websocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'update_room_group',
            {
                'type': 'update_rooms',
                'data': 'start'
            }
        )

def gamePhase(current_round):
    nextTrick(0, current_round)
    sendGameUpdate(current_round.room, 'launch_game_phase')

def betPhase(room):
    nextRound(room)
    sendGameUpdate(room, 'launch_bet_phase')

def playCard(request, room, data):
    user = request.user
    current_player = Player.objects.get(user=user, rooms=room)
    current_round = room.rounds.all().latest('value')
    try:
        current_trick = Trick.objects.filter(round=current_round).latest('value')
    except Trick.DoesNotExist:
        return
    # Vérifier tour de jeu
    if playerTurn(current_trick) == current_player:
        card_name = data.get('card_name')
        print(card_name)
        if card_name == "tigress0" or card_name == "tigress1":
            current_round.tigressOption = (card_name[7] == "1")
            current_round.save()
            card_name = "tigress"
        card_association = CardAssociation.objects.get(round=current_round, card__name=card_name)
        if canBePlayed(card_association, current_trick):
            card_association.trick = current_trick
            card_association.save()
            sendGameUpdate(room, 'new_card_played')
            time.sleep(1)
            if CardAssociation.objects.filter(round=current_round, trick=current_trick).count() == room.players.count() :
                # Passer au tour suivant si tout le monde a joué
                current_trick.player = defineTrickWinner(current_trick)
                current_trick.save()
                nextTrick(current_trick.value, current_round)

def getOrderedPlayers(trick):
    trick_number = trick.value
    players = trick.round.room.players.all()
    if trick_number == 1:
        current_dealer = trick.round.player
        user_index = next((i for i, player in enumerate(players) if player == current_dealer), None)
        return list(players[user_index + 1:]) + list(players[:user_index]) + [current_dealer]
    else:
        last_trick = Trick.objects.get(round=trick.round, value=trick_number-1)
        first_player = last_trick.player
        user_index = next((i for i, player in enumerate(players) if player == first_player), None)
        return [first_player] + list(players[user_index + 1:]) + list(players[:user_index])

def defineTrickWinner(trick):
    max_card = None
    ordered_players = getOrderedPlayers(trick)
    # Cartes spéciales
    pirates = CardAssociation.objects.filter(trick=trick, card__type="pirate") 
    if trick.round.tigressOption:
        tigresses = CardAssociation.objects.filter(trick=trick, card__type="tigress")
        pirates = pirates.union(tigresses)
    sirens = CardAssociation.objects.filter(trick=trick, card__type="siren") 
    skullking = CardAssociation.objects.filter(trick=trick, card__type="skullking")
    if skullking.exists() or (sirens.exists() and not pirates.exists()):
        if sirens.exists():
            # Récupère la première sirene jouée
            sirens_players = [siren.hand.player for siren in sirens]
            for player in ordered_players:
                if player in sirens_players:
                    max_card = sirens.get(hand__player=player)
                    break
        else:
            max_card = skullking.first()
    elif pirates.exists():
        # Récupère le premier pirate joué
        pirates_players = [pirate.hand.player for pirate in pirates]
        for player in ordered_players:
            if player in pirates_players:
                max_card = pirates.get(hand__player=player)
                break
    else:
        # Aucune carte spéciale maitresse jouée
        colors = ["black", "green", "purple", "yellow"]
        for player in ordered_players:
            asked_color = CardAssociation.objects.get(hand__player=player, trick=trick).card.type
            if asked_color in colors:
                break
        if asked_color in ["green", "purple", "yellow"]:
            # Récupère la meilleur carte à la couleur demandé
            max_value = CardAssociation.objects.filter(trick=trick, card__type=asked_color).aggregate(Max('card__value'))['card__value__max']
            max_card = CardAssociation.objects.get(trick=trick, card__type=asked_color, card__value=max_value) 
        # S'il y a des atouts, change la carte maitresse par le meilleur atout
        trumps = CardAssociation.objects.filter(trick=trick, card__type="black")
        if trumps.exists():
            max_value = trumps.aggregate(Max('card__value'))['card__value__max']
            max_card = CardAssociation.objects.get(trick=trick, card__type="black", card__value=max_value) 
    # Si personne n'est vainqueur, alors le premier joueur remporte le pli
    if max_card is None:
        max_card = CardAssociation.objects.get(hand__player=ordered_players[0], trick=trick)
    return max_card.hand.player

def playerTurn(trick):
    if trick is None:
        return None
    ordered_players = getOrderedPlayers(trick)
    if CardAssociation.objects.filter(trick=trick).exists() == False: # Premier jouer à jouer
        return ordered_players[0]
    else: # Un joueur ou plus à déjà joué
        for player in ordered_players:
            if not CardAssociation.objects.filter(hand__player=player, trick=trick).exists():
                return player

def canBePlayed(played_card, trick):
    colors = ["black", "green", "purple", "yellow"]
    if not CardAssociation.objects.filter(trick=trick).exists(): # Premier à jouer
        return True
    if played_card.card.type not in colors: # Joue une carte spéciale
        return True
    else:
        ordered_players = getOrderedPlayers(trick)
        for player in ordered_players:
            try:
                asked_color = CardAssociation.objects.get(round=trick.round, hand__player=player, trick=trick).card.type
                # Ne reporte le choix de la couleur demandé que si fuite
                if not (asked_color == "escape" or (asked_color == "tigress" and trick.round.tigressOption == 0)):
                    break
            except CardAssociation.DoesNotExist:
                break
        if asked_color not in colors: # Il n'y a pas encore eu de carte de couleur de jouée
            return True
        hand = CardAssociation.objects.filter(round=trick.round, hand=played_card.hand, trick__isnull=True)
        if asked_color != played_card.card.type and hand.filter(card__type=asked_color).exists():
            return False
    return True

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
    sendGameUpdate(room, 'new_bet')
    if Bet.objects.filter(round=current_round).count() == room.players.all().count():
        gamePhase(current_round)

def calculScore(current_round):
    players = current_round.room.players.all()

    for player in players:
        tricks = Trick.objects.filter(round=current_round, player=player)
        bet = Bet.objects.get(round=current_round, player=player)
        if bet.value == tricks.count():
            # Pari respecté
            if bet.value == 0: # + 10 points par carte
                player.score += current_round.value * 10
            else: # +20 points par carte + Cartes bonus
                player.score += bet.value * 20
                valuableCards = CardAssociation.objects.filter(card__value=14, trick__player=player, round=current_round)
                for valuableCard in valuableCards:
                    if valuableCard.card.type == "black":
                        player.score += 20
                    else:
                        player.score += 10
                skullkingWinnerTrick = CardAssociation.objects.filter(card__type="skullking",  round=current_round, trick__player=player, hand__player=player)
                if skullkingWinnerTrick.exists():
                    piratesInTrick = CardAssociation.objects.filter(card__type="pirate", trick=skullkingWinnerTrick.first().trick)
                    if current_round.tigressOption:
                        tigresses = CardAssociation.objects.filter(card__type="tigress", trick=skullkingWinnerTrick.first().trick)
                        piratesInTrick = piratesInTrick.union(tigresses)
                    player.score += piratesInTrick.count() * 30
                sirenWinnerTricks = CardAssociation.objects.filter(card__type="siren",  round=current_round, trick__player=player, hand__player=player)
                for sirenTrick in sirenWinnerTricks:
                    player.score += CardAssociation.objects.filter(card__type="skullking", trick=sirenTrick.trick).exists() * 40
                pirateWinnerTricks = CardAssociation.objects.filter(card__type="pirate",  round=current_round, trick__player=player, hand__player=player)
                for pirateTrick in pirateWinnerTricks:
                    player.score += CardAssociation.objects.filter(card__type="siren", trick=pirateTrick.trick).count() * 20
        else:
            # Pari raté
            if bet.value == 0: # - 10 points par carte
                player.score -= current_round.value * 10
            else: # - 10 points par pli d'écart
                player.score -= abs(bet.value - tricks.count()) * 10
        player.save()
    sendGameUpdate(current_round.room, 'scores')