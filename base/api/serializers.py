from rest_framework.serializers import ModelSerializer
from base import models


class UserSerializer(ModelSerializer):
    class Meta:
        model = models.User
        exclude = ['password']


class LocationSerializer(ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'


class PaymentMethodSerializer(ModelSerializer):
    class Meta:
        model = models.PaymentMethod
        fields = '__all__'


class CarMethodSerializer(ModelSerializer):
    class Meta:
        model = models.CardMethod
        exclude = ['security_code']


class EBankingMethodSerializer(ModelSerializer):
    class Meta:
        model = models.EBankingMethod
        fields = '__all__'


class PaymentHistorySerializer(ModelSerializer):
    class Meta:
        model = models.PaymentHistory
        fields = '__all__'


class ChatRoomSerializer(ModelSerializer):
    class Meta:
        model = models.ChatRoom
        fields = '__all__'


class MessageSerializer(ModelSerializer):
    class Meta:
        model = models.Message
        fields = '__all__'


class CourseSerializer(ModelSerializer):
    class Meta:
        model = models.Course
        fields = '__all__'


class TrainingSessionSerializer(ModelSerializer):
    class Meta:
        model = models.TrainingSession
        fields = '__all__'


class BookingSessionSerializer(ModelSerializer):
    class Meta:
        model = models.BookingSession
        fields = '__all__'
