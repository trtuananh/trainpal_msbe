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
        

class LocationForm(ModelForm):
    class Meta:
        model = models.Location
        exclude = ['user']


class PaymentForm(ModelForm):
    class Meta:
        model = models.Payment
        exclude = ['sender', 'receiver']


class ChatRoomForm(ModelForm):
    class Meta:
        model = models.ChatRoom
        exclude = ['host']
        fields = '__all__'


class MessageForm(ModelForm):
    class Meta:
        model = models.Message
        exclude = ['sender']


class CourseForm(ModelForm):
    class Meta:
        model = models.Course
        exclude = ['trainer']


class TrainingSessionForm(ModelForm):
    class Meta:
        model = models.TrainingSession
        fields = '__all__'


class BookingSessionForm(ModelForm):
    class Meta:
        model = models.BookingSession
        exclude = ['user']


class RatingForm(ModelForm):
    class Meta:
        model = models.Rating
        exclude = ['user']
