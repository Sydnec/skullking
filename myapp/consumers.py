# myapp/consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
# from myapp.views.game import display

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'room_updates'
        self.room_group_name = 'update_room_group'

        # Rejoindre le groupe de mise à jour de la salle
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe de mise à jour de la salle
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def update_rooms(self, event):
            await self.send(text_data=json.dumps({
                'message': 'update_rooms',
                'type': event['type'],
                'data': event['data']
            }))

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'game_updates'
        self.room_group_name = 'update_game_group'

        # Rejoindre le groupe de mise à jour du jeu
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe de mise à jour du jeu
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def update_game(self, event):
        await self.send(text_data=json.dumps({
            'message': 'update_game',
            'type': event['type'],
            'room_id': event['room_id'],
            'data': event['data']
        }))

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logging.info("WebSocket Connected")
        await self.accept()

    async def disconnect(self, close_code):
        logging.info("WebSocket Disconnected")

    async def receive(self, text_data):
        logging.info(f"Message received: {text_data}")
        await self.send(text_data="Message received!")