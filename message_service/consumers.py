import json
import requests
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from . import models

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.access_token = self.scope['access_token']
        
        # Verify user via user_service
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{self.user_id}/",
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code != 200:
            await self.close()
            return

        self.room_group_name = f'chat_{self.user_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        room_id = data['room_id']
        message = data['message']

        try:
            chat_room = models.ChatRoom.objects.get(id=room_id)
            if int(self.user_id) not in chat_room.user_ids:
                await self.send(text_data=json.dumps({
                    'error': 'You are not a member of this chat room'
                }))
                return

            # Save message
            msg = models.Message.objects.create(
                sender_id=self.user_id,
                room=chat_room,
                message=message
            )

            # Update last seen
            last_seen = models.LastSeen.objects.get(user_id=self.user_id, room=chat_room)
            last_seen.last_seen = timezone.now()
            last_seen.save()

            # Send message to all users in the room
            for user_id in chat_room.user_ids:
                await self.channel_layer.group_send(
                    f'chat_{user_id}',
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': msg.id,
                            'sender_id': msg.sender_id,
                            'room_id': msg.room_id,
                            'message': msg.message,
                            'created': msg.created.isoformat()
                        }
                    }
                )
        except models.ChatRoom.DoesNotExist:
            await self.send(text_data=json.dumps({
                'error': 'Chat room not found'
            }))
        except models.LastSeen.DoesNotExist:
            await self.send(text_data=json.dumps({
                'error': 'Last seen not found'
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
        