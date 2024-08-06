from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# region > User

class Sport(models.Model):
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
        WEIGHTLIFTING = "WL", _("Weight Lifting")

    name = models.CharField(unique=True, max_length=20, choices=SportName.choices)
    image = models.ImageField(null=True, blank=True)
    icon = models.ImageField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    email = models.EmailField(unique=True)
    isTrainer = models.BooleanField(default=False)

    class Gender(models.TextChoices):
        MALE = "M", _("Male")
        FEMALE = "F", _("Female")
        NOTSPECIFY = "N", _("Not specify")
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.NOTSPECIFY, blank=True)
    dob = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(default="avatar.svg")
    
    sports = models.ManyToManyField(Sport, related_name='sports')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


# endregion


# region > Location

class Location(models.Model):
    name = models.CharField(max_length=200, blank=True)
    address = models.TextField()
    image = models.ImageField(blank=True, null=True)
    user = models.ForeignKey(User, models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user}: {self.address[:20]}"

# endregion


# region > Payment

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, models.CASCADE, null=True)

    class PaymentType(models.TextChoices):
        CARD = "CD", _("Card")
        EBANKING = "EB", _("E-Banking")
        CASH = "CS", _("Cash")
    
    payment_type = models.CharField(max_length=2, choices=PaymentType.choices)

    def __str__(self) -> str:
        return f"{self.user}: {self.payment_type}"


class CardMethod(models.Model):
    payment_method = models.OneToOneField(PaymentMethod, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=200)
    card_number = models.CharField(max_length=16, validators=[RegexValidator(r'^\d{16}$')])
    expire_date = models.CharField(max_length=5, 
                                   validators=[RegexValidator(r'^(0[1-9]|1[0-2])\/[0-9]{2}$')])
    security_code = models.CharField(max_length=3, validators=[RegexValidator(r'^[0-9]{3}$')])

    class CardType(models.TextChoices):
        CREDIT = "CR", _("Credit")
        DEBIT = "DB", _("Debit")

    card_type = models.CharField(max_length=2, choices=CardType.choices)

    def __str__(self) -> str:
        return f"{self.owner_name}: {self.card_type}"


class EBankingMethod(models.Model):
    payment_method = models.OneToOneField(PaymentMethod, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=200)
    account_id = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return f"{self.owner_name}: {self.bank_name}"


class PaymentHistory(models.Model):
    sender = models.ForeignKey(User, models.SET_NULL, null=True, related_name="sender")
    receiver = models.ForeignKey(User, models.SET_NULL, null=True, related_name="receiver")

    send_method = models.ForeignKey(PaymentMethod, models.SET_NULL, null=True, related_name="send_method")
    receive_method = models.ForeignKey(PaymentMethod, models.SET_NULL, null=True, related_name="receive_method")

    value = models.IntegerField()
    message = models.CharField(max_length=1000, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.send_method} to {self.receive_method}: {self.value}"


# endregion


# region > Messages

class ChatRoom(models.Model):
    name = models.CharField(max_length=500, blank=True)
    host = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='host')
    users = models.ManyToManyField(User)


class Message(models.Model):
    sender = models.ForeignKey(User, models.SET_NULL, null=True)
    room = models.ForeignKey(ChatRoom, models.CASCADE)
    content = models.TextField()

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return f"{self.sender} to {self.room}: {self.content}"

# endregion


# region > Booking

class Course(models.Model):
    trainer = models.ForeignKey(User, models.CASCADE, null=True)
    sport = models.ForeignKey(Sport, models.RESTRICT)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True)
    location = models.TextField()
    
    class CourseLevel(models.IntegerChoices):
        BEGINNER = 0
        INTERMEDIATE = 1
        ADVANCED = 2
    level = models.IntegerField(choices=CourseLevel.choices)
    unit_session = models.FloatField(default=1.0) # hours
    unit_price = models.IntegerField()

    max_trainee = models.IntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.title[:50]} - {self.trainer}"


class TrainingSession(models.Model):
    course = models.ForeignKey(Course, models.SET_NULL, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    room = models.ForeignKey(ChatRoom, models.SET_NULL, blank=True, null=True)

    class SessionState(models.TextChoices):
        AVAILABLE = "AV", _("Available")
        UPCOMING = "UP", _("Up Coming")
        DURING = "DR", _("During Training")
        FINISH = "FN", _("Finished")

    state = models.CharField(max_length=2, choices=SessionState.choices, default=SessionState.AVAILABLE)

    class Meta:
        ordering = ['start']

    def __str__(self) -> str:
        return f"{self.course}: from {self.start} in {self.duration} hours"


class BookingSession(models.Model):
    user = models.ForeignKey(User, models.RESTRICT)
    payment_history = models.ForeignKey(PaymentHistory, models.RESTRICT, blank=True, null=True)
    training_session = models.ForeignKey(TrainingSession, models.RESTRICT)

    def __str__(self) -> str:
        return f"{self.user}: {self.training_session.course}"


class Rating(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    booking_session = models.ForeignKey(BookingSession, models.CASCADE)
    rating = models.FloatField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course} - {self.user} ({self.rating}/5)"

# endregion
