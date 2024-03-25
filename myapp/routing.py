# myapp/routing.py

# * https://github.com/learningnoobi/django_channels_bingo_game

from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from myapp.consumers import RoomConsumer

websocket_urlpatterns = [
    path('ws/room_updates/', RoomConsumer.as_asgi()),
]