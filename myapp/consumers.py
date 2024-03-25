# myapp/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('room_updates', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('room_updates', self.channel_name)

    async def update_rooms(self, event):
        await self.send(text_data=json.dumps({
            'message': 'update_rooms',
            'type': event['type'],
            'data': event['data']
        }))
