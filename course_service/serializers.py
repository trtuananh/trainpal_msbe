from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.utils import timezone
from datetime import timedelta
from . import models
import requests

class LocationSerializer(ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'

class CourseSerializer(ModelSerializer):
    trainer = SerializerMethodField()
    weekly_sessions = SerializerMethodField()
    location = LocationSerializer(read_only=True)

    def get_trainer(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.trainer_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json()
        return {}

    def get_weekly_sessions(self, obj):
        today = timezone.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return TrainingSessionSerializer(
            obj.training_sessions.filter(start__gte=start_of_week, start__lte=end_of_week),
            context={'request': self.context['request']},
            many=True
        ).data

    class Meta:
        model = models.Course
        fields = '__all__'

class MinimalCourseSerializer(ModelSerializer):
    location = SerializerMethodField()

    def get_location(self, obj):
        return obj.location.name if obj.location else None

    class Meta:
        model = models.Course
        fields = ['id', 'title', 'location', 'sport', 'unit_price', 'unit_session', 'max_trainee']

class BookingSessionSerializer(ModelSerializer):
    course = MinimalCourseSerializer(read_only=True)
    n_members = SerializerMethodField()
    is_booked = SerializerMethodField()
    user = SerializerMethodField()

    def get_n_members(self, obj):
        if obj.training_session:
            return obj.training_session.booking_sessions.count()
        return 0

    def get_is_booked(self, obj):
        return obj.training_session is not None and obj.user_id == self.context['request'].user.id

    def get_user(self, obj):
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{obj.user_id}/",
            headers={'Authorization': self.context['request'].headers.get('Authorization', '')}
        )
        if response.status_code == 200:
            return response.json()
        return {}

    class Meta:
        model = models.BookingSession
        fields = '__all__'

class TrainingSessionSerializer(ModelSerializer):
    course = MinimalCourseSerializer(read_only=True)
    n_members = SerializerMethodField()
    is_booked = SerializerMethodField()
    price = SerializerMethodField()

    def get_n_members(self, obj):
        return obj.booking_sessions.count()

    def get_price(self, obj):
        price = sum(booking_session.price for booking_session in obj.booking_sessions.all())
        return price

    def get_is_booked(self, obj):
        user = self.context['request'].user
        if obj.course.trainer_id == user.id:
            return obj.booking_sessions.count() > 0
        return obj.booking_sessions.filter(user_id=user.id).exists()

    class Meta:
        model = models.TrainingSession
        fields = '__all__'

class TrainingSessionDetailSerializer(TrainingSessionSerializer):
    course = CourseSerializer(read_only=True)
    booking_sessions = BookingSessionSerializer(many=True, read_only=True)

    class Meta:
        model = models.TrainingSession
        fields = '__all__'

class RatingSerializer(ModelSerializer):
    class Meta:
        model = models.Rating
        fields = '__all__'
