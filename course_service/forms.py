from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from . import models  


class LocationForm(ModelForm):
    class Meta:
        model = models.Location
        exclude = ['user']


class PaymentForm(ModelForm):
    class Meta:
        model = models.Payment
        exclude = ['sender', 'receiver']


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
