from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from . import models


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = models.User
        fields = ['first_name', "last_name", 'username', 'isTrainer', 'email', 'password1', 'password2']


class UserForm(ModelForm):
    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'username', 'email', 'isTrainer',
                  'gender', 'dob', 'bio', 'phone', 'avatar']
  