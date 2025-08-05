from django.db import models
from django.utils.translation import gettext_lazy as _

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

class Course(models.Model):
    trainer_id = models.IntegerField()
    sport = models.CharField(max_length=2, choices=SportName.choices)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True)
    
    class CourseLevel(models.IntegerChoices):
        BEGINNER = 0
        INTERMEDIATE = 1
        ADVANCED = 2

    level = models.IntegerField(choices=CourseLevel.choices)
    unit_session = models.FloatField(default=1.0)  # hours
    unit_price = models.IntegerField()
    min_trainee = models.IntegerField(default=1, blank=True)
    max_trainee = models.IntegerField(default=1, blank=True)
    star = models.FloatField(default=3.0, blank=True)

    def __str__(self) -> str:
        return f"{self.title[:50]} - Trainer ID: {self.trainer_id}"

class Location(models.Model):
    name = models.CharField(max_length=200, blank=True)
    lng = models.FloatField()
    lat = models.FloatField()
    course = models.OneToOneField(Course, models.CASCADE, related_name="location", null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.course}: {self.name[:20]}"

class TrainingSession(models.Model):
    course = models.ForeignKey(Course, models.SET_NULL, null=True, related_name="training_sessions")
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        ordering = ['start']

    def __str__(self) -> str:
        return f"{self.course}: from {self.start} to {self.end}"

class BookingSession(models.Model):
    user_id = models.IntegerField()
    course = models.ForeignKey(Course, models.SET_NULL, null=True, related_name="booking_sessions")
    start = models.DateTimeField()
    end = models.DateTimeField()
    training_session = models.ForeignKey(TrainingSession, models.RESTRICT, blank=True, null=True, related_name="booking_sessions")
    price = models.IntegerField()
    payment_id = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"User ID: {self.user_id}: {self.start} to {self.end}"

class Rating(models.Model):
    user_id = models.IntegerField()
    course = models.ForeignKey(Course, models.SET_NULL, null=True, related_name="ratings")
    booking_session = models.OneToOneField(BookingSession, models.CASCADE)
    rating = models.FloatField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course} - User ID: {self.user_id} ({self.rating}/5)"