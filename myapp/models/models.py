# myapp/models/model.py

import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Card(models.Model): # Model des cartes. Il y en a 70 décrites dans cards.yaml
    VALUE_CHOICES = [
        (i, str(i)) for i in range(15)
    ]
    TYPE_CHOICES = [
        ('yellow', 'yellow'),
        ('purple', 'purple'),
        ('green', 'green'),
        ('black', 'black'),
        ('pirate', 'pirate'),
        ('siren', 'siren'),
        ('skullking', 'skullking'),
        ('escape', 'escape'),
        ('tigress', 'tigress'),
    ]
    value = models.IntegerField(choices=VALUE_CHOICES, default=0)
    name = models.CharField(max_length=20, default='')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='black')

class Player(models.Model): # Player fait le lien entre user et les autres classes
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

class Room(models.Model): # Stock les players
    code = models.CharField(max_length=6, unique=True,  primary_key=True)
    players = models.ManyToManyField(Player, related_name='rooms', blank=True, limit_choices_to={'rooms__lt': 8})
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_rooms')

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        # Génère un code aléatoire de 6 caractères
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Round(models.Model): # Value : 1..10, Appartient à 1 room, Stock les bets, associe à chacune des 70 cartes
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='rounds')
    bets = models.ManyToManyField('Bet', related_name='rounds', blank=True, limit_choices_to={'rounds__lt': 10})
    value = models.IntegerField(default=1, choices=[(i, i) for i in range(1, 11)])
    cards = models.ManyToManyField(Card, through='CardAssociation')

@receiver(post_save, sender=Round)
def create_card_associations(sender, instance, created, **kwargs):
    if created:
        cards = Card.objects.all()
        for card in cards:
            CardAssociation.objects.create(round=instance, card=card)

class Bet(models.Model): # Appartient à 1 joueur et 1 round. Value : 0..10
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    value = models.IntegerField(default=0, choices=[(i, i) for i in range(11)]) 

class Hand(models.Model): # Appartient à 1 joueur. 
    player = models.OneToOneField(Player, on_delete=models.CASCADE)

class Trick(models.Model): # Appatient à 1 joueur et 1 round
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)

class Message(models.Model): # Appartient à 1 joueur et 1 room
    room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True)

class CardAssociation(models.Model): # Relie chaque carte à hand ou trick. Appartient à 1 round
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    hand = models.ForeignKey(Hand, on_delete=models.CASCADE, blank=True, null=True)
    trick = models.ForeignKey(Trick, on_delete=models.CASCADE, blank=True, null=True)