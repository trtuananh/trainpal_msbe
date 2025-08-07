from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

# from . import forms


# region > User

class SportName(models.TextChoices):
    BADMINTON = "BM", _("Badminton")
    BASKETBALL = "BK", _("Basketball")
    BOXING = "BX", _("Boxing")
    FOOTBALL = "FB", _("Football")
    GYM = "GY", _("Gym")
    KICKBOXING = "KB", _("Kickboxing")
    SWIMMING = "SW", _("Swimming")
    TENNIS = "TN", _("Tennis")
    VOLEYBALL = "VB", _("Voleyball")
    YOGA = "YG", _("Yoga")
    PICKLEBALL = "PB", _("Pickleball")
    # WEIGHTLIFTING = "WL", _("Weight Lifting")


class User(AbstractUser):
    email = models.EmailField(unique=False) # TODO: change to true after testing
    isTrainer = models.BooleanField(blank=True, default=False)

    class Gender(models.TextChoices):
        MALE = "M", _("Male")
        FEMALE = "F", _("Female")
        NOTSPECIFY = "N", _("Not specify")

    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True, default=Gender.NOTSPECIFY)
    dob = models.DateTimeField(blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    refresh_token = models.TextField()
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('refresh_token', 'device_id')


class Course(models.Model):
    trainer = models.ForeignKey(User, models.CASCADE, null=True, related_name="courses")
    sport = models.CharField(max_length=2, choices=SportName.choices)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True)
    # location = models.TextField(default="Your location", blank=True)
    
    class CourseLevel(models.IntegerChoices):
        BEGINNER = 0
        INTERMEDIATE = 1
        ADVANCED = 2

    level = models.IntegerField(choices=CourseLevel.choices)
    unit_session = models.FloatField(default=1.0) # hours
    unit_price = models.IntegerField()

    min_trainee = models.IntegerField(default=1, blank=True)
    max_trainee = models.IntegerField(default=1, blank=True)
    star = models.FloatField(default=3.0, blank=True)

    def __str__(self) -> str:
        return f"{self.title[:50]} - {self.trainer}"

# endregion


# region > Location

class Location(models.Model):
    name = models.CharField(max_length=200, blank=True)
    lng = models.FloatField()
    lat = models.FloatField()
    course = models.OneToOneField(Course, models.CASCADE, related_name="location", null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.course}: {self.name[:20]}"

# endregion


# region > Payment

class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        ONLINE = "ONL", _("Online")
        OFFLINE = "OFF", _("Offline")

    sender = models.ForeignKey(User, models.SET_NULL, null=True, 
                               related_name="sending_payments")
    receiver = models.ForeignKey(User, models.SET_NULL, null=True, 
                                 related_name="receiving_payments")

    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=3, choices=PaymentMethod.choices)

    value = models.IntegerField()
    payment_info = models.CharField(max_length=1000, blank=True)
    momo_transaction_id = models.CharField(max_length=100, blank=True)
    momo_payment_type = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False, blank=True)
    success = models.BooleanField(default=False, blank=True)
    message = models.CharField(max_length=1000, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.sender} to {self.receiver}: {self.value}"

# endregion


# region > Messages

class ChatRoom(models.Model):
    name = models.CharField(max_length=500, blank=True)
    host = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='host')
    users = models.ManyToManyField(User, related_name="chat_rooms")

    # def __str__(self) -> str:
    #     return f"{self.name}: {self.users.all()[0]}, ..."


class Message(models.Model):
    sender = models.ForeignKey(User, models.SET_NULL, null=True, related_name="messages")
    room = models.ForeignKey(ChatRoom, models.CASCADE, related_name="messages")
    content = models.TextField()

    date = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     ordering = ['-date']

    def __str__(self) -> str:
        return f"@{self.sender}: {self.content}"


class LastSeen(models.Model):
    user = models.ForeignKey(User, models.CASCADE, related_name="last_seens")
    room = models.ForeignKey(ChatRoom, models.CASCADE, related_name="last_seens")
    date = models.DateTimeField(auto_now=True)
    unique_together = ('user', 'room')

# endregion


# region > Booking

class TrainingSession(models.Model):
    course = models.ForeignKey(Course, models.SET_NULL, null=True, 
                               related_name="training_sessions")
    start = models.DateTimeField()
    end = models.DateTimeField()
    room = models.ForeignKey(ChatRoom, models.SET_NULL, blank=True, null=True, 
                             related_name="training_sessions")

    class Meta:
        ordering = ['start']

    def __str__(self) -> str:
        return f"{self.course}: from {self.start} to {self.end} in {self.end - self.start} hours"


class BookingSession(models.Model):
    user = models.ForeignKey(User, models.RESTRICT, related_name="booking_sessions")

    course = models.ForeignKey(Course, models.SET_NULL, null=True, related_name="booking_sessions")
    start = models.DateTimeField()
    end = models.DateTimeField()
    training_session = models.ForeignKey(TrainingSession, models.RESTRICT, blank=True, null=True, 
                                         related_name="booking_sessions")

    price = models.IntegerField()
    payment = models.ForeignKey(Payment, models.CASCADE, blank=True, null=True, 
                                related_name="booking_sessions")

    def __str__(self) -> str:
        return f"{self.user}: {self.start} to {self.end}"


class Rating(models.Model):
    user = models.ForeignKey(User, models.CASCADE, related_name="ratings")
    course = models.ForeignKey(Course, models.SET_NULL, null=True, related_name="ratings")
    booking_session = models.OneToOneField(BookingSession, models.CASCADE)
    rating = models.FloatField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course} - {self.user} ({self.rating}/5)"

# endregion
