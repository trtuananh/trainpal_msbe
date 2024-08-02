from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from . import models


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = models.User
        fields = ['first_name', "last_name", 'username', 'email', 'password1', 'password2']


# class RoomForm(ModelForm):
#     class Meta:
#         model = Room
#         fields = '__all__'
#         exclude = ['host', 'participants']


class UserForm(ModelForm):
    class Meta:
        model = models.User
        # fields = ['first_name', 'last_name']
        fields = ['first_name', 'last_name', 'username', 'email', 'isTrainer',
                  'gender', 'dob', 'bio', 'phone', 'avatar', 'sports']
        

class LocationForm(ModelForm):
    class Meta:
        model = models.Location
        fields = '__all__'
