from rest_framework.serializers import ModelSerializer
from base import models


class UserSerializer(ModelSerializer):
    class Meta:
        model = models.User
        # fields = '__all__'
        exclude = ['password']


class LocationSerializer(ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'
