import random
import string
from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

class Room(models.Model):
    code = models.CharField(max_length=6, unique=True,  primary_key=True)
    players = models.ManyToManyField(Player, related_name='rooms', blank=True, limit_choices_to={'rooms__lt': 10})
    rounds = models.ManyToManyField('Round', related_name='rooms', blank=True, limit_choices_to={'rooms__lt': 10})
    owner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='owned_rooms', null=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        # Génère un code aléatoire de 6 caractères
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Round(models.Model):
    bets = models.ManyToManyField('Bet', related_name='rounds', blank=True, limit_choices_to={'rounds__lt': 10})
    players = models.ManyToManyField(Player, related_name='rounds', blank=True, limit_choices_to={'rounds__lt': 10})
    value = models.IntegerField(default=1, choices=[(i, i) for i in range(1, 11)])

class Bet(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    value = models.IntegerField(default=1, choices=[(i, i) for i in range(1, 11)]) 

class Hand(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)

class Fold(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)

class Card(models.Model):
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
    round = models.ForeignKey(Round, on_delete=models.CASCADE, blank=True, null=True)
    fold = models.ForeignKey(Fold, on_delete=models.CASCADE, blank=True, null=True)
    hand = models.ForeignKey(Hand, on_delete=models.CASCADE, blank=True, null=True)
    value = models.IntegerField(choices=VALUE_CHOICES, default=0)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='black')

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True)
