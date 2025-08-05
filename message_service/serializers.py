from rest_framework.serializers import ModelSerializer, SerializerMethodField
from . import models
import requests

class MessageSerializer(ModelSerializer):
    sender = SerializerMethodField()

    def get_sender(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.sender_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json().get('username', '')
        return ''

    class Meta:
        model = models.Message
        fields = '__all__'

class LastSeenSerializer(ModelSerializer):
    user = SerializerMethodField()

    def get_user(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.user_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json().get('username', '')
        return ''

    class Meta:
        model = models.LastSeen
        fields = '__all__'

class ChatRoomSerializer(ModelSerializer):
    users = SerializerMethodField()
    booking_session = SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    last_seens = LastSeenSerializer(many=True, read_only=True)

    def get_users(self, obj):
        users = []
        for user_id in obj.user_ids:
            response = requests.get(
                f"http://localhost:8000/api/user/profile/{user_id}/",
                headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
            )
            if response.status_code == 200:
                users.append(response.json().get('username', ''))
        return users

    def get_booking_session(self, obj):
        if obj.booking_session_id:
            response = requests.get(
                f"http://localhost:8000/api/course/booking/{obj.booking_session_id}/",
                headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
            )
            if response.status_code == 200:
                return response.json()
        return None

    class Meta:
        model = models.ChatRoom
        fields = '__all__'
        