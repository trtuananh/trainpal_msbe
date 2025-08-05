from rest_framework.serializers import ModelSerializer, SerializerMethodField
from . import models
import requests

class PaymentSerializer(ModelSerializer):
    sender = SerializerMethodField()
    receiver = SerializerMethodField()
    booking_sessions = SerializerMethodField()

    def get_sender(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.sender_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json().get('username', '')
        return ''

    def get_receiver(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.receiver_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json().get('username', '')
        return ''

    def get_booking_sessions(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/course/booking-by-payment/{obj.id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json()
        return []

    class Meta:
        model = models.Payment
        fields = '__all__'
        depth = 1
        