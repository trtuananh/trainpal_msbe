from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        if self.scope["user"].is_anonymous:
            print("Token is invalid or expired")
            await self.close(code=4004, reason="Token is invalid or expired")
            return

        self.user = self.scope["user"]
        self.user_id = self.scope['url_route']['kwargs']['user_id']

        # Kiểm tra quyền truy cập
        if str(self.user.id) != str(self.user_id):
            await self.close(code=4001, reason="You are not allowed to access this chat")
            return

        self.room_name = f'chat_{self.user_id}'
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            print(f"Discard room: {self.room_name}")
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )

    async def receive(self, text_data):
        from web_base.api.serializers import UserListSerializer
        from channels.db import database_sync_to_async

        data = json.loads(text_data)
        print("data:", data)
        message = data['message']
        sender = self.user.id
        room = int(data['room'])

        print(f"Received message: {message} from {sender} to {room}")
        try:
            @database_sync_to_async
            def get_room_users():
                room_obj = self.user.chat_rooms.get(id=room)
                return room_obj, list(room_obj.users.all())
            
            room_obj, users = await get_room_users()
        except Exception as e:
            print(f"Room {room} does not belong to user {self.user.id}:", e)
            self.close(code=4001, reason="You are not allowed to access this chat")
            return

        for user in users:
            await self.channel_layer.group_send(
                f'chat_{user.id}',
                {
                    'type': 'chat_message',
                    'content': message,
                    'sender': sender,
                    'room': room,
                    'date': data.get('date')
                }
            )

        # Lưu tin nhắn vào database (nếu cần)
        await self.save_message(self.user, room_obj, message, data.get('date'))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'content': event['content'],
            'sender': event['sender'],
            'room': event['room'],
            'date': event['date']
        }))

    async def save_message(self, sender, room, content, date):
        from web_base.models import Message
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def save_message_sync():
            Message.objects.create(
                sender=sender,
                room=room,
                content=content,
                date=date
            )
        
        await save_message_sync()
