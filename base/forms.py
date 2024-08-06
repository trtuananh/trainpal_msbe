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
        fields = ['first_name', 'last_name', 'username', 'email', 'isTrainer']
        # fields = ['first_name', 'last_name', 'username', 'email', 'isTrainer',
        #           'gender', 'dob', 'bio', 'phone', 'avatar', 'sports']
        

class LocationForm(ModelForm):
    class Meta:
        model = models.Location
        exclude = ['user']


class PaymentMethodForm(ModelForm):
    class Meta:
        model = models.PaymentMethod
        # fields = ["payment_type", "info"]
        exclude = ['user']


class CardMethodForm(ModelForm):
    class Meta:
        model = models.CardMethod
        exclude = ['payment_method']


class EBankingMethodForm(ModelForm):
    class Meta:
        model = models.EBankingMethod
        exclude = ['payment_method']


class PaymentHistoryForm(ModelForm):
    class Meta:
        model = models.PaymentHistory
        exclude = ['sender']


class ChatRoomForm(ModelForm):
    class Meta:
        model = models.ChatRoom
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
