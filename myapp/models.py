from django.db import models

class Player(models.Model):
    score = models.IntegerField()

# class Bet(models.Model):
#     player = models.ForeignKey(Player, on_delete=models.CASCADE)
#     value = models.DecimalField(max_digits=5, decimal_places=2)

# class Room(models.Model):
#     id = models.CharField(default=get_random_string(6), max_length=6, primary_key=True)
#     players = models.ManyToManyField(Player)

# class Round(models.Model):
#     room = models.ForeignKey(Room, on_delete=models.CASCADE)
#     value = models.IntegerField()
#     bets = models.ManyToManyField(Bet)
