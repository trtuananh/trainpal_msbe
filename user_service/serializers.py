from rest_framework.serializers import ModelSerializer
from . import models

class UserSerializer(ModelSerializer):
    class Meta:
        model = models.User
        exclude = ['password']

class UserListSerializer(ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']
        